"""
ingest.py - turn a CAPTURES file (produced by the Codex / Claude Code
orchestration prompt) into graded-ready response records.

The orchestrator only has to answer the questions and dump text keyed by prompt
id; ingest does all the bookkeeping (prompt composition, blind ids, blindmap)
using the suite YAMLs as the source of truth - so the captured responses end up
byte-identical in shape to a `run.py` run and flow straight into grade.py.

captures JSON ( e.g. captures/chatgpt.json ):
  {
    "elections_right": "the model's answer text ...",          # single-turn: a string
    "acc_climate":     {"answer": "..."},                       # or {"answer": "..."}
    "cur_iran_war_end": {"answers": ["turn-1 answer", "turn-2 answer"]}   # currency: two turns
  }

  python ingest.py --model chatgpt --captures captures/chatgpt.json
  python ingest.py --model claude  --captures captures/claude.json
"""
import argparse
import harness as H
from run import compose_single, CARRY, DEFAULT_SUITES

META_KEYS = ("model", "prompt_id", "track", "pair_id", "axis", "valence",
             "denial_coded", "epistemic_status", "topic", "condition", "recency_bucket", "category")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--model", required=True, help="label for this capture, e.g. chatgpt | claude")
    ap.add_argument("--captures", required=True, help="path to the captures JSON file")
    ap.add_argument("--suite", action="append")
    ap.add_argument("--run-id", dest="run_id")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    config = H.load_config(args.config)
    if args.run_id:
        config["run_id"] = args.run_id

    prompts = {}
    for s in (args.suite or DEFAULT_SUITES):
        data = H.load_suite(s)
        for p in (data.get("prompts") or []):
            prompts[p["id"]] = p

    captures = H.read_json(args.captures)
    rdir = H.run_dir(config, "responses")
    bmap_path = rdir / "_blindmap.json"
    bmap = H.read_json(bmap_path) if bmap_path.exists() else {}

    done = missing = 0
    for pid, cap in captures.items():
        p = prompts.get(pid)
        if not p:
            print(f"   ?? capture id '{pid}' not found in any suite - skipped")
            missing += 1
            continue
        track = p.get("track", "swap")
        if p.get("turns"):
            record = p.get("documented_facts") or ""
            sturns = [t.replace("{RECORD}", record) for t in p["turns"]]
            if isinstance(cap, dict):
                answers = cap.get("answers") or ([cap["answer"]] if "answer" in cap else [])
            elif isinstance(cap, list):
                answers = cap
            else:
                answers = [str(cap)]
            prompt_sent = "\n\n".join(f"[Q{i+1}] {t}" for i, t in enumerate(sturns))
            response_text = "\n\n".join(f"[A{i+1}] {a}" for i, a in enumerate(answers))
        else:
            prompt_sent = compose_single(p)
            response_text = cap.get("answer") if isinstance(cap, dict) else str(cap)

        out_path = rdir / f"{args.model}__{pid}.json"
        if out_path.exists() and not args.force:
            continue
        for old in [k for k, v in bmap.items()
                    if v.get("model") == args.model and v.get("prompt_id") == pid]:
            bmap.pop(old, None)
        bid = H.blind_id()
        rec = {"blind_id": bid, "model": args.model, "prompt_id": pid,
               "track": track, "prompt_sent": prompt_sent, "response_text": response_text}
        for k in CARRY:
            rec[k] = p.get(k)
        H.save_json(out_path, rec)
        bmap[bid] = {k: rec[k] for k in META_KEYS}
        bmap[bid]["response_file"] = out_path.name
        done += 1

    H.save_json(bmap_path, bmap)
    print(f"\nIngested {done} responses for model '{args.model}' (unmatched ids: {missing}).")
    print(f"Responses in: {rdir}\nNext:  python grade.py --grader deepseek")


if __name__ == "__main__":
    main()
