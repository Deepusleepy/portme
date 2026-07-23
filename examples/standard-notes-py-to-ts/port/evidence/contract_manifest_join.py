#!/usr/bin/env python3
"""Contract<->manifest join + cross-artifact integrity (errata passes 2 and 4).

Validates:
  Manifest schema — exact finalized header and non-empty check_inputs per unit.
  Surface/NF coverage — every contract surface maps to a manifest unit, or (for
    intentionally-divergent rows) to an approved divergence; NF-001..003 owned.
  (a) every judge scenario surface_id exists in the contract.
  (b) every accepted-divergence surface exists in the contract AND that row is
      marked intentionally-divergent.
  (c) every behavior-map contract_id exists in the contract (surface or NF).
  (d) no citation-bearing artifact cites a DELETED bare ID (S3 / S6).
Run from the published example root. Exits non-zero on any problem.
"""
import csv, re, sys

EXPECTED_MANIFEST_COLUMNS = [
    'unit_id', 'source_scope', 'target_paths', 'depends_on', 'contract_ids',
    'rule_ids', 'gap_ids', 'check_inputs', 'unit_check', 'risk',
]

def cells(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]

# --- contract surfaces + NF ---
surfaces = {}   # id -> standard
nfs = []
for line in open('port/contract.md'):
    m = re.match(r'\|\s*(S\d+[a-z]?)\s*\|', line)
    if m:
        surfaces[m.group(1)] = cells(line)[4].lower()
    m2 = re.match(r'\|\s*(NF-\d+)\s*\|', line)
    if m2:
        nfs.append(m2.group(1))
valid_ids = set(surfaces) | set(nfs)

# --- approved divergences ---
div_rows = []
with open('port/accepted-divergences.tsv') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        if r['id'].startswith('D-'):
            div_rows.append((r['id'], r['surface']))
div_ids = {d for d, _ in div_rows}

# --- manifest schema + cited ids ---
problems = []
out = []
cited = {}
with open('port/manifest.tsv') as f:
    reader = csv.DictReader(f, delimiter='\t')
    if reader.fieldnames != EXPECTED_MANIFEST_COLUMNS:
        problems.append(
            f"manifest header mismatch: expected {EXPECTED_MANIFEST_COLUMNS}, "
            f"got {reader.fieldnames}")
    manifest_rows = list(reader)
    for r in manifest_rows:
        if r['unit_id'].startswith('#'): continue
        if not r.get('check_inputs', '').strip():
            problems.append(f"manifest unit {r['unit_id']} has empty check_inputs")
        for i in [x for x in re.split(r'[ ,]+', r['contract_ids']) if x]:
            cited.setdefault(i, []).append(r['unit_id'])

out.append("=== Manifest authorization schema ===")
out.append("  header: " +
           ("OK (check_inputs between gap_ids and unit_check)"
            if not any(p.startswith('manifest header mismatch') for p in problems)
            else "MISMATCH"))
out.append("  check_inputs: " +
           ("all units declared" if not any('empty check_inputs' in p for p in problems)
            else "MISSING"))

out.append("=== Surface coverage ===")
for sid in sorted(surfaces, key=lambda s: (int(re.match(r'S(\d+)', s).group(1)), s)):
    std = surfaces[sid]; owners = cited.get(sid, [])
    if 'intentionally-divergent' in std:
        dref = re.search(r'D-\d+', std, re.IGNORECASE)
        did = dref.group(0).upper() if dref else None
        ok = bool(did) and did in div_ids
        status = f"divergence {did or '??'}" + ("" if ok else " MISSING-DIVERGENCE")
    else:
        ok = bool(owners); status = ("units " + ",".join(owners)) if owners else "UNCOVERED"
    if not ok: problems.append(f"surface {sid}: {status}")
    out.append(f"  {sid:5} [{std:26}] -> {status}")

out.append("=== Non-functional coverage ===")
for nf in nfs:
    owners = cited.get(nf, [])
    if not owners: problems.append(f"NF {nf}: UNCOVERED")
    out.append(f"  {nf} -> {'units '+','.join(owners) if owners else 'UNCOVERED'}")

out.append("=== Orphan check (manifest cites nonexistent id) ===")
orphans = sorted(i for i in cited if i not in valid_ids)
for o in orphans:
    problems.append(f"orphan manifest id {o} (units {cited[o]})")
    out.append(f"  ORPHAN {o} cited by {cited[o]}")
if not orphans: out.append("  none")

out.append("=== (a) judge scenarios.tsv surface_ids exist in contract ===")
with open('port/judge/scenarios.tsv') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        if r['scenario_id'].startswith('#'): continue
        for sid in [x for x in re.split(r'[ ,]+', r['surface_id']) if x]:
            ok = sid in valid_ids
            if not ok: problems.append(f"scenario {r['scenario_id']} cites unknown surface {sid}")
            out.append(f"  {r['scenario_id']:7} {sid:5} {'OK' if ok else 'UNKNOWN'}")

out.append("=== (b) divergence surfaces exist + are intentionally-divergent ===")
for did, surf in div_rows:
    exists = surf in surfaces
    div = exists and 'intentionally-divergent' in surfaces[surf]
    status = "OK" if div else ("NOT-IN-CONTRACT" if not exists else "NOT-MARKED-DIVERGENT")
    if not div: problems.append(f"divergence {did} surface {surf}: {status}")
    out.append(f"  {did} -> {surf:5} {status}")

out.append("=== (c) behavior-map contract_ids exist ===")
bm_bad = 0
with open('port/behavior-map.tsv') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        if r['unit_id'].startswith('#'): continue
        for i in [x for x in re.split(r'[ ,]+', r.get('contract_ids','')) if x]:
            if i not in valid_ids:
                problems.append(f"behavior-map row {r['unit_id']}/{r['from_node']} cites unknown {i}")
                out.append(f"  {r['unit_id']} {r['from_node']} -> {i} UNKNOWN"); bm_bad += 1
out.append("  (all behavior-map contract_ids valid)" if bm_bad == 0 else f"  {bm_bad} invalid")

out.append("=== (d) no citation-bearing artifact cites a DELETED bare ID (S3/S6) ===")
scan = ['port/contract.md', 'port/manifest.tsv', 'port/behavior-map.tsv',
        'port/gaps.tsv', 'port/rulebook.md', 'port/accepted-divergences.tsv',
        'port/judge/scenarios.tsv', 'port/judge/scenarios.sh']
dead = re.compile(r'(?<![A-Za-z0-9])S[36](?![0-9a-z])')  # bare S3/S6, not S3a/S6b/S30...
d_hits = 0
for path in scan:
    try: text = open(path).read()
    except FileNotFoundError: continue
    for n, ln in enumerate(text.splitlines(), 1):
        if dead.search(ln):
            problems.append(f"{path}:{n} cites deleted bare ID: {ln.strip()[:80]}")
            out.append(f"  DEAD-ID {path}:{n}"); d_hits += 1
if d_hits == 0:
    out.append("  none — no deleted bare S3/S6 in citation-bearing artifacts")

print("\n".join(out))
print(f"\nPROBLEMS: {len(problems)}")
for p in problems: print(f"  - {p}")
print(f"\nJOIN+INTEGRITY: {'PASS' if not problems else 'FAIL'}")
sys.exit(1 if problems else 0)
