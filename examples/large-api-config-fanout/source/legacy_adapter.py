#!/usr/bin/env python3
import argparse, json, os, sys

DEFAULTS = {"timeout_ms": 1000, "retries": 2, "region": "us-east", "strict": True}
ALLOWED = set(DEFAULTS)

def load_config(path, args):
    cfg = dict(DEFAULTS)
    if path:
        data = json.load(open(path, encoding="utf-8"))
        unknown = sorted(set(data) - ALLOWED)
        if unknown:
            raise ValueError("unknown config keys: " + ", ".join(unknown))
        cfg.update(data)
    if "PORTME_TIMEOUT_MS" in os.environ:
        cfg["timeout_ms"] = int(os.environ["PORTME_TIMEOUT_MS"])
    if args.timeout_ms is not None: cfg["timeout_ms"] = args.timeout_ms
    if args.retries is not None: cfg["retries"] = args.retries
    if args.region is not None: cfg["region"] = args.region
    if cfg["timeout_ms"] <= 0: raise ValueError("timeout_ms must be positive")
    if not 0 <= cfg["retries"] <= 5: raise ValueError("retries must be between 0 and 5")
    if cfg["region"] not in ("us-east", "eu-west"): raise ValueError("unsupported region")
    return cfg

def translate(req, cfg):
    if sorted(req) != ["payload", "user_id"]: raise ValueError("request must contain only user_id and payload")
    if not isinstance(req["user_id"], (str, int)): raise ValueError("user_id must be string or integer")
    return {"subject": {"id": str(req["user_id"])}, "data": req["payload"], "meta": {"region": cfg["region"], "timeoutMs": cfg["timeout_ms"], "maxAttempts": cfg["retries"] + 1}}

def execute(plan, sequence):
    attempts = 0
    statuses = [int(x) for x in sequence.split(",") if x]
    while True:
        status = statuses[min(attempts, len(statuses)-1)] if statuses else 200
        attempts += 1
        if status != 503 or attempts >= plan["meta"]["maxAttempts"]:
            break
    return {"attempts": attempts, "status": status, "ok": 200 <= status < 300, "request": plan, "error": None if status < 400 else ("temporary" if status == 503 else "upstream")}

def main():
    p=argparse.ArgumentParser(prog="legacy-adapter")
    p.add_argument("command", choices=["plan","run"]); p.add_argument("--config"); p.add_argument("--request", required=True)
    p.add_argument("--timeout-ms", type=int); p.add_argument("--retries", type=int); p.add_argument("--region")
    p.add_argument("--sequence", default="200")
    a=p.parse_args()
    try:
        cfg=load_config(a.config,a); req=json.loads(a.request); plan=translate(req,cfg)
        out=plan if a.command=="plan" else execute(plan,a.sequence)
        print(json.dumps(out, sort_keys=True, separators=(",",":"))); return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("error: "+str(exc), file=sys.stderr); return 2
if __name__ == "__main__": raise SystemExit(main())
