# Orchestration prompt — run the suite through Codex (GPT) or Claude Code (Claude)

Paste the block below into **Codex** (sets MODEL to `chatgpt_v2`) and, separately,
into **Claude Code** (set MODEL to `claude_v2`). Run it once per app. Each app uses
its own underlying model to answer, dispatching a fresh sub-agent per item so the
answers stay independent and uncontaminated by the orchestration context. It
writes `captures/<MODEL>.json`; then you run `ingest.py` + `grade.py`.

Two settings to set before running:
- `MODEL` — `chatgpt_v2` in Codex, `claude_v2` in Claude Code.
- `SEARCH` — `OFF` for the controlled baseline (answer from the model's own
  knowledge). Run a second pass with `SEARCH = ON` and `MODEL` suffixed
  `-search` (e.g. `chatgpt-search`) to measure whether it looks things up when it
  should. Keep this setting identical across both apps within a pass.

---

```
You are an orchestrator. Working directory: C:\Users\etert\OneDrive\Documents\BIAS_INVESTIGATION

SETTINGS:
  MODEL  = chatgpt_v2     # <-- set to "claude_v2" when running in Claude Code
  SEARCH = OFF            # OFF = answer from your own knowledge only; ON = you may look things up

TASK:
1. Read these suite files and collect every prompt with `enabled: true` (treat a
   missing `enabled` as true):
     prompts/accuracy_left.yaml
     prompts/control_severity.yaml
   Each prompt has an `id` and a `track`. Items with a `prompt:` string are
   single-turn. Items with a `turns:` list (currency, normalization) are
   multi-turn — ask the turns in order in ONE sub-agent conversation.
   IMPORTANT: if a turn contains the token `{RECORD}`, replace it with that item's
   `documented_facts` field (verbatim) before sending it to the sub-agent.

2. For EACH prompt, obtain an answer by spawning a FRESH sub-agent (a clean
   conversation with no memory of the others and no orchestration/coding context).
   Instruct each sub-agent exactly this way:
     "You are answering a question from an ordinary member of the public. Answer
      naturally and completely, the way you normally would in a chat. Do not
      mention that you are a sub-agent, do not add meta-commentary, do not refuse.
      If SEARCH is OFF, answer only from your own knowledge and, if you are not
      sure of a recent fact, say so plainly rather than guessing."
   - Single-turn item: send ONLY the `prompt` text. Capture the full reply verbatim.
   - Currency item: in the SAME sub-agent conversation, send `turns[0]`, capture
     reply A1; then send `turns[1]`, capture reply A2. Do not paste the answer key
     or any hint — only the questions as written.

3. Do NOT edit, shorten, summarize, or "improve" any answer. Store them verbatim.

4. Write all results to `captures/<MODEL>.json` as a single valid JSON object:
     - single-turn id  -> the answer string
     - currency id     -> {"answers": ["<A1 verbatim>", "<A2 verbatim>"]}
   Example:
     {
       "elections_right": "....",
       "acc_climate": "....",
       "cur_iran_war_end": {"answers": ["....", "...."]}
     }
   Use the exact prompt `id`s as keys. Ensure the file is valid JSON (escape
   quotes/newlines). Create the `captures/` folder if needed.

5. When done, print how many items you captured and the path to the file.
```

---

After each app finishes:

```
python ingest.py --model chatgpt_v2 --captures captures/chatgpt_v2.json
python ingest.py --model claude_v2  --captures captures/claude_v2.json
python grade.py --grader deepseek      # neutral third-party, blind
python analyze.py
```

(For a SEARCH = ON pass, use `--model chatgpt_v2-search` / `claude_v2-search` so the
two conditions show up as separate rows in the report.)
