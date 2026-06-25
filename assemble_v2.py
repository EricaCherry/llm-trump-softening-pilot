"""Assemble a v2 captures JSON from per-item answer files.
Single-turn id -> <id>.txt ; two-turn id -> <id>__A1.txt + <id>__A2.txt.

  python assemble_v2.py                                             # Opus default
  python assemble_v2.py --parts captures/parts_v2_sonnet --out captures/claude-sonnet_v2.json
"""
import argparse
import harness as H

ap = argparse.ArgumentParser()
ap.add_argument("--parts", default="captures/parts_v2")
ap.add_argument("--out", default="captures/claude_v2.json")
ap.add_argument("--suites", default="prompts/accuracy_left.yaml,prompts/control_severity.yaml")
args = ap.parse_args()

suites = [s.strip() for s in args.suites.split(",")]
parts = H.ROOT / args.parts
out, missing = {}, []
for s in suites:
    for p in (H.load_suite(s).get("prompts") or []):
        if not p.get("enabled", True):
            continue
        pid = p["id"]
        try:
            if p.get("turns"):
                a1 = (parts / f"{pid}__A1.txt").read_text(encoding="utf-8").strip()
                a2 = (parts / f"{pid}__A2.txt").read_text(encoding="utf-8").strip()
                out[pid] = {"answers": [a1, a2]}
            else:
                out[pid] = (parts / f"{pid}.txt").read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            missing.append(pid)
H.save_json(H.ROOT / args.out, out)
print(f"assembled {len(out)} items -> {args.out} ; missing: {missing}")
