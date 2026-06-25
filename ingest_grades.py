"""
ingest_grades.py - fold an externally-produced grades file (e.g. GPT/Codex output)
into the per-grader grades dir, so it joins the same analysis as the other graders.

Accepts either:
  {"r_abc123": {"severity":4, ...}, ...}            # dict keyed by blind_id
  [{"blind_id":"r_abc123", "severity":4, ...}, ...]  # list of objects

  python ingest_grades.py --grader gpt --file grading/pilot/gpt_grades.json
"""
import argparse
import harness as H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--grader", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--run-id", dest="run_id")
    args = ap.parse_args()

    config = H.load_config(args.config)
    if args.run_id:
        config["run_id"] = args.run_id
    rdir = H.run_dir(config, "responses")
    bmap = H.read_json(rdir / "_blindmap.json")
    gdir = H.run_dir(config, "grades") / args.grader

    data = H.read_json(args.file)
    if isinstance(data, dict) and isinstance(data.get("grades"), list):
        data = data["grades"]          # unwrap {"grades": [...]} export format
    if isinstance(data, list):
        data = {d["blind_id"]: d for d in data}

    n = miss = 0
    for bid, scores in data.items():
        meta = bmap.get(bid)
        if not meta:
            miss += 1
            continue
        out = {k: v for k, v in scores.items() if k != "blind_id"}
        out.update({"blind_id": bid, "grader": args.grader,
                    "track": meta.get("track", "swap")})
        H.save_json(gdir / f"{bid}.json", out)
        n += 1
    print(f"Ingested {n} grades for grader '{args.grader}' (unmatched blind_ids: {miss}).")
    print(f"Grades in: {gdir}")


if __name__ == "__main__":
    main()
