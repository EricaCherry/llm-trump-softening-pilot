"""Rebuild the blind-map from response files on disk (salvages any orphaned
captures whose run never wrote the blind-map). Each response file carries its own
full record, so we can reconstruct the blind-map entry from it."""
import collections
import harness as H

config = H.load_config("config.yaml")
rp = H.run_dir(config, "responses")
bmp = rp / "_blindmap.json"
bm = H.read_json(bmp) if bmp.exists() else {}
known = {v.get("response_file") for v in bm.values()}
mk = ("model", "prompt_id", "track", "pair_id", "axis", "valence", "denial_coded",
      "epistemic_status", "topic", "condition", "recency_bucket")
added = 0
for f in sorted(rp.glob("*.json")):
    if f.name == "_blindmap.json" or f.name in known:
        continue
    rec = H.read_json(f)
    bid = rec.get("blind_id")
    if not bid:
        continue
    for k in [k for k, v in bm.items()
              if v.get("model") == rec.get("model") and v.get("prompt_id") == rec.get("prompt_id")]:
        bm.pop(k, None)
    bm[bid] = {k: rec.get(k) for k in mk}
    bm[bid]["response_file"] = f.name
    added += 1
H.save_json(bmp, bm)
print(f"reconciled: added {added} | blindmap now {len(bm)}")
print(dict(collections.Counter(v["model"] for v in bm.values())))
