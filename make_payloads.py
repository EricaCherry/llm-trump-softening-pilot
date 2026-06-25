"""
make_payloads.py - build ONE set of blinded grading payloads that every grader
(DeepSeek API, Claude sub-agents, GPT/Codex) scores identically. Writes:
  grading/<run_id>/payloads.json        - list of {blind_id, track, dims, payload}
  grading/<run_id>/batches/batch_NN.json - same, split for parallel sub-agents
The payload is the full track-specific rubric + the question/transcript + the
response, with NO model identity (blind). Reuses grade.py's rubrics verbatim.
"""
import argparse
import math
import harness as H
from grade import build_payload, DIMS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--run-id", dest="run_id")
    ap.add_argument("--batches", type=int, default=7)
    ap.add_argument("--missing-grader", help="only include items lacking a grade from this grader")
    args = ap.parse_args()

    config = H.load_config(args.config)
    if args.run_id:
        config["run_id"] = args.run_id
    rdir = H.run_dir(config, "responses")
    bmap = H.read_json(rdir / "_blindmap.json")
    skip_dir = (H.run_dir(config, "grades") / args.missing_grader) if args.missing_grader else None

    items = []
    for bid, meta in bmap.items():
        if skip_dir is not None and (skip_dir / f"{bid}.json").exists():
            continue
        rec = H.read_json(rdir / meta["response_file"])
        track = rec.get("track", "swap")
        items.append({"blind_id": bid, "track": track,
                      "dims": DIMS[track], "payload": build_payload(rec, track)})

    gdir = H.ROOT / "grading" / str(config.get("run_id", "pilot"))
    (gdir / "batches").mkdir(parents=True, exist_ok=True)
    H.save_json(gdir / "payloads.json", items)
    size = max(1, math.ceil(len(items) / args.batches))
    n = 0
    for i in range(0, len(items), size):
        H.save_json(gdir / "batches" / f"batch_{n:02d}.json", items[i:i + size])
        n += 1
    print(f"{len(items)} payloads -> {n} batches in {gdir / 'batches'}")
    print(f"all-in-one: {gdir / 'payloads.json'}")


if __name__ == "__main__":
    main()
