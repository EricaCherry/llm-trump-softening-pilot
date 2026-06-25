"""
run.py - send the prompt suite(s) to each configured model and save raw responses.

Three tracks:
  swap     - valence-swapped pairs (naive/asymmetry bias)
  accuracy - cited settled-fact claims (unwarranted-balance)
  currency - multi-turn probe for a key recent fact the model may lack

  python run.py --mock                                  # offline dry-run
  python run.py --model deepseek                         # one model, real
  python run.py --suite prompts/accuracy_settled.yaml    # one suite
  python run.py --include-disabled --mock --run-id test  # exercise enabled:false items
"""
import argparse
import harness as H

DEFAULT_SUITES = ["prompts/suite_pilot.yaml",
                  "prompts/accuracy_settled.yaml",
                  "prompts/currency_gaps.yaml",
                  "prompts/trump_currency.yaml",
                  "prompts/normalization_severity.yaml",
                  "prompts/control_severity.yaml",
                  "prompts/matrix_severity.yaml"]

CARRY = ("pair_id", "axis", "valence", "denial_coded", "epistemic_status",
         "topic", "condition", "ground_truth", "sources", "claim",
         "key_fact", "fact_date", "recency_bucket", "documented_facts", "category")


def compose_single(p):
    if p.get("condition") == "fact" and p.get("facts"):
        return f"Documented facts:\n{p['facts'].rstrip()}\n\n{p['prompt'].rstrip()}"
    return p["prompt"].rstrip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--suite", action="append")
    ap.add_argument("--model", action="append")
    ap.add_argument("--run-id", dest="run_id")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--include-disabled", action="store_true")
    args = ap.parse_args()

    config = H.load_config(args.config)
    if args.run_id:
        config["run_id"] = args.run_id
    settings = {"mock": args.mock,
                "sentinel": config.get("capture", {}).get("response_sentinel", "<<<END>>>")}

    prompts = []
    for s in (args.suite or DEFAULT_SUITES):
        data = H.load_suite(s)
        if data and data.get("prompts"):
            prompts.extend(data["prompts"])
    if not args.include_disabled:
        prompts = [p for p in prompts if p.get("enabled", True)]

    models = config["models"]
    if args.model:
        models = [m for m in models if m["name"] in args.model]

    rdir = H.run_dir(config, "responses")
    bmap_path = rdir / "_blindmap.json"
    bmap = H.read_json(bmap_path) if bmap_path.exists() else {}

    done = skipped = 0
    for m in models:
        for p in prompts:
            track = p.get("track", "swap")
            out_path = rdir / f"{m['name']}__{p['id']}.json"
            if out_path.exists() and not args.force:
                skipped += 1
                continue
            try:
                if p.get("turns"):
                    record = p.get("documented_facts") or ""
                    sturns = [t.replace("{RECORD}", record) for t in p["turns"]]
                    history, responses, aborted = [], [], False
                    for i, t in enumerate(sturns):
                        txt = H.call_turn(t, history, m, settings,
                                          turn_label=f"[TURN {i+1}/{len(sturns)}]",
                                          first_turn=(i == 0))
                        if txt is None:
                            aborted = True
                            break
                        history += [{"role": "user", "content": t},
                                    {"role": "assistant", "content": txt}]
                        responses.append(txt)
                    if aborted:
                        print(f"   skipped {m['name']} / {p['id']}")
                        continue
                    prompt_sent = "\n\n".join(f"[Q{i+1}] {t}" for i, t in enumerate(sturns))
                    response_text = "\n\n".join(f"[A{i+1}] {r}" for i, r in enumerate(responses))
                else:
                    prompt_sent = compose_single(p)
                    response_text = H.call_model(prompt_sent, m, settings)
            except Exception as e:
                print(f"\n!! {m['name']} / {p['id']} FAILED: {e}")
                continue
            if response_text is None:
                print(f"   skipped {m['name']} / {p['id']}")
                continue

            # drop stale blind entries for this (model, prompt) before re-adding
            for old in [k for k, v in bmap.items()
                        if v.get("model") == m["name"] and v.get("prompt_id") == p["id"]]:
                bmap.pop(old, None)
            bid = H.blind_id()
            rec = {"blind_id": bid, "model": m["name"], "prompt_id": p["id"],
                   "track": track, "prompt_sent": prompt_sent,
                   "response_text": response_text}
            for k in CARRY:
                rec[k] = p.get(k)
            H.save_json(out_path, rec)
            meta_keys = ("model", "prompt_id", "track", "pair_id", "axis", "valence",
                         "denial_coded", "epistemic_status", "topic", "condition",
                         "recency_bucket", "category")
            bmap[bid] = {k: rec[k] for k in meta_keys}
            bmap[bid]["response_file"] = out_path.name
            done += 1

    H.save_json(bmap_path, bmap)
    print(f"\nDone. captured={done}, skipped(existing)={skipped}, blind entries={len(bmap)}")
    print(f"Responses in: {rdir}")
    print("Next:  python grade.py --grader human   (or --grader deepseek / --mock)")


if __name__ == "__main__":
    main()
