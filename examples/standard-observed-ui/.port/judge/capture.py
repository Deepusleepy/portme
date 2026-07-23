#!/usr/bin/env python3
"""capture.py — the observed-only raw-capture pipeline for Pocket Tasks.

Executes the full flow required by references/no-source.md:
  quarantine (outside repo, 0700, non-symlink)
    -> raw source capture
    -> regular-file/symlink inventory + hashes
    -> named scanner (pocketscan) scan, receipt preserved outside fixtures
    -> redaction in quarantine + rescan
    -> copy-not-link admission of redacted regular files into judge fixtures
    -> admitted-copy verification (regular, non-symlink, hashes)
    -> quarantine deletion + path-absent verification
    -> capture receipt

Usage: capture.py <source_base_url>

Nothing here is destructive to the repo; the only deletion target is the
freshly created quarantine directory whose resolved path is recorded first.
"""
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PORT_ROOT = os.path.abspath(os.path.join(HERE, ".."))          # .port
TARGET_ROOT = os.path.abspath(os.path.join(PORT_ROOT, ".."))    # ui-target
FIX = os.path.join(HERE, "fixtures")
RECEIPTS = os.path.join(PORT_ROOT, "receipts")
SCANNER = os.path.join(PORT_ROOT, "scanner", "pocketscan.py")
RULES = os.path.join(PORT_ROOT, "scanner", "pocketscan-rules.json")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def main():
    if len(sys.argv) < 2:
        print("usage: capture.py <source_base_url>", file=sys.stderr)
        return 2
    source = sys.argv[1]
    cap_id = "001"
    rec = []
    rec.append("## Capture receipt — %s" % cap_id)
    rec.append("- Generated: %s" % now())

    # 1. Quarantine outside the repository.
    quar = tempfile.mkdtemp(prefix="pocketcap-")
    quar = os.path.realpath(quar)
    os.chmod(quar, 0o700)
    is_symlink = os.path.islink(quar)
    mode = oct(os.stat(quar).st_mode & 0o777)
    inside_repo = os.path.commonpath([quar, TARGET_ROOT]) == TARGET_ROOT
    assert not inside_repo, "quarantine must be outside the repo"
    assert not is_symlink and mode == "0o700"
    rec.append("- Authorization: preauthorized local dogfood matrix (see status.md); "
               "account/environment: assistant-owned local fixture at %s" % source)
    rec.append("- Quarantine: %s; mode: %s; non-symlink: %s; outside-repo: %s"
               % (quar, mode, "yes" if not is_symlink else "NO", "yes"))

    raw_dir = os.path.join(quar, "raw")

    try:
        # 2. Raw source capture into quarantine.
        rc, out, err = run([sys.executable, os.path.join(HERE, "run_source.py"),
                            source, raw_dir])
        assert rc == 0, "source capture failed: %s" % err
        raw_files = sorted(os.path.join(raw_dir, f) for f in os.listdir(raw_dir))

        # 3. Inventory: reject any non-regular / symlink entries; hash the rest.
        rejected = []
        inv = []
        for root, dirs, files in os.walk(raw_dir):
            for name in dirs + files:
                p = os.path.join(root, name)
                if os.path.islink(p):
                    rejected.append("symlink:%s" % p)
                    continue
                st = os.lstat(p)
                import stat as _stat
                if os.path.isdir(p):
                    continue
                if not _stat.S_ISREG(st.st_mode):
                    rejected.append("non-regular:%s" % p)
                    continue
                inv.append((os.path.relpath(p, quar), sha256_file(p)))
        inv_path = os.path.join(PORT_ROOT, "evidence", "capture-%s-inventory.txt" % cap_id)
        with open(inv_path, "w") as f:
            f.write("# Quarantine inventory (regular files only) — %s\n" % now())
            f.write("# quarantine=%s\n" % quar)
            for rel, digest in inv:
                f.write("%s  %s\n" % (digest, rel))
            f.write("# rejected entries: %s\n" % (rejected or "none"))
        rec.append("- Inventory: %d regular files (see evidence/capture-%s-inventory.txt); "
                   "rejected entries: %s" % (len(inv), cap_id, rejected or "none"))

        # 4. Scanner over raw capture; preserve raw receipt OUTSIDE fixtures.
        rules_digest = sha256_file(RULES)
        rc_scan, scan_out, scan_err = run(
            [sys.executable, SCANNER, "scan", "--rules", RULES, "--json", raw_dir])
        scan_report_path = os.path.join(RECEIPTS, "capture-%s-scan-raw.json" % cap_id)
        with open(scan_report_path, "w") as f:
            f.write(scan_out)
        scan_report = json.loads(scan_out)
        raw_findings = scan_report["finding_count"]
        ver_rc, ver_out, _ = run([sys.executable, SCANNER, "--version"])
        rec.append("- Scanner: %s; config: scanner/pocketscan-rules.json + SHA-256 %s; "
                   "command: pocketscan scan --rules <rules> --json <raw>; "
                   "exit=%d; raw findings=%d; receipt: receipts/capture-%s-scan-raw.json"
                   % (ver_out.strip(), rules_digest, rc_scan, raw_findings, cap_id))

        # 5. Redact in quarantine, then rescan the redacted output.
        red_dir = os.path.join(quar, "redacted")
        rc_red, red_out, red_err = run(
            [sys.executable, SCANNER, "redact", "--rules", RULES, "--out", red_dir, raw_dir])
        assert rc_red == 0, red_err
        rc_rescan, rescan_out, _ = run(
            [sys.executable, SCANNER, "scan", "--rules", RULES, "--json", red_dir])
        rescan_report = json.loads(rescan_out)
        rescan_findings = rescan_report["finding_count"]
        rescan_path = os.path.join(RECEIPTS, "capture-%s-rescan-redacted.json" % cap_id)
        with open(rescan_path, "w") as f:
            f.write(rescan_out)
        assert rescan_findings == 0, "redacted output still has findings!"
        rec.append("- Redaction/rescan: pocketscan redact -> rescan clean (findings=%d); "
                   "receipt: receipts/capture-%s-rescan-redacted.json"
                   % (rescan_findings, cap_id))

        # 6. Admit redacted regular files: COPY (never link) into fixtures/<id>/.
        admitted = []
        for red_file in sorted(os.listdir(red_dir)):
            sid = red_file[:-len(".json")] if red_file.endswith(".json") else red_file
            src_hash = None
            raw_match = os.path.join(raw_dir, red_file)
            if os.path.exists(raw_match):
                src_hash = sha256_file(raw_match)
            dest_dir = os.path.join(FIX, sid)
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, "observation.json")
            shutil.copyfile(os.path.join(red_dir, red_file), dest)  # copy, not link
            # 7. Verify the admitted copy is a regular, non-symlink file.
            assert not os.path.islink(dest) and os.path.isfile(dest)
            assert os.stat(dest).st_nlink == 1, "admitted copy is hard-linked"
            admitted.append((sid, src_hash, sha256_file(dest)))
        adm_path = os.path.join(PORT_ROOT, "evidence", "capture-%s-admitted.txt" % cap_id)
        with open(adm_path, "w") as f:
            f.write("# Admitted redacted copies — %s\n" % now())
            f.write("# scenario_id  raw_source_sha256  admitted_fixture_sha256\n")
            for sid, sh, dh in admitted:
                f.write("%s  %s  %s\n" % (sid, sh, dh))
        rec.append("- Admitted copies: %d redacted regular files (see "
                   "evidence/capture-%s-admitted.txt); link checks (symlink/hardlink): passed"
                   % (len(admitted), cap_id))

    finally:
        # 8. Delete quarantine and verify the resolved path is gone.
        deletion_ok = False
        if os.path.exists(quar):
            shutil.rmtree(quar)
        deletion_ok = not os.path.exists(quar)
        rec.append("- Deletion: shutil.rmtree(%s) at %s; path-absent verification: %s"
                   % (quar, now(), "confirmed absent" if deletion_ok else "FAILED — RESIDUAL"))
        if not deletion_ok:
            print("FATAL: quarantine deletion failed, residual at %s" % quar, file=sys.stderr)

    receipt_path = os.path.join(RECEIPTS, "capture-%s.md" % cap_id)
    with open(receipt_path, "w") as f:
        f.write("\n".join(rec) + "\n")
    print("capture pipeline complete -> %s" % receipt_path)
    print("\n".join(rec))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
