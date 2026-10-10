## Capture receipt: 001
- Generated: 2026-07-23T05:01:17Z
- Authorization: preauthorized local dogfood matrix (see status.md); account/environment: assistant-owned local fixture at http://127.0.0.1:18765
- Quarantine: REDACTED-LOCAL-FIXTURE/pocketcap-5xao8jki; mode: 0o700; non-symlink: yes; outside-repo: yes
- Inventory: 18 regular files (see evidence/capture-001-inventory.txt); rejected entries: none
- Scanner: pocketscan 1.0.0; config: scanner/pocketscan-rules.json + SHA-256 9772277db2440aa756dfe689ade6c3e1253a9295214f6147cb304f88f96f22a9; command: pocketscan scan --rules <rules> --json <raw>; exit=1; raw findings=8; receipt: receipts/capture-001-scan-raw.json
- Redaction/rescan: pocketscan redact -> rescan clean (findings=0); receipt: receipts/capture-001-rescan-redacted.json
- Admitted copies: 18 redacted regular files (see evidence/capture-001-admitted.txt); link checks (symlink/hardlink): passed
- Deletion: shutil.rmtree(REDACTED-LOCAL-FIXTURE/pocketcap-5xao8jki) at 2026-07-23T05:01:18Z; path-absent verification: confirmed absent
