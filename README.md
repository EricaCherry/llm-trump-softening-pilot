# multi-reply-ai-bias-analysis

A reusable harness for measuring how large language models frame politically
charged questions, scored blind by multiple independent graders.

> ## AI models consistently sane-wash Trump
>
> Across three model families, LLMs understate the severity of Trump's documented
> wrongdoing on the first reply — more than for any comparable figure, including
> his own convictions — and revise only once shown the record.
> **Full write-up: [FINDINGS.md](FINDINGS.md).**

![First-reply softening gap by subject](assets/softening_gap.svg)

## Method

The harness runs four measurement tracks. The headline result comes from the
**first-reply softening** track:

- **softening** — a two-turn probe: the model answers a charged question, then
  answers again after a sourced record is supplied. The gap between the two
  measures how far the first reply falls short of the model's own
  evidence-informed judgment. Each model serves as its own control.
- **accuracy** — does the model state citation-anchored settled facts plainly, or
  false-balance them?
- **currency** — does the model know recent developments, and when it doesn't,
  does it flag the gap or confabulate?
- **swap** — symmetry of framing across matched prompts.

Responses are graded **blind** by two independent graders (a DeepSeek model and
GPT-via-Codex); a grader never sees which model produced a response.

## Run

```
pip install -r requirements.txt
cp config.example.yaml config.yaml     # add a DeepSeek API key
python run.py
python grade.py --grader deepseek-flash
python analyze.py --grader deepseek-flash --grader codex
```

App-based models (ChatGPT, Claude) can be captured via the orchestration prompt in
`ORCHESTRATE.md`; see `GRADE_GPT.md` for the GPT grader lane.

## Repository structure

| path | contents |
|---|---|
| `prompts/` | prompt suites (one per track / subject set) |
| `harness.py` · `run.py` · `grade.py` · `analyze.py` · `ingest.py` | the pipeline |
| `rubric.md` | scoring definitions |
| `FINDINGS.md` | the write-up |
| `assets/` | figures |
| `analysis/pilot/` | scored report (`report.md`) and joined data (`joined.csv`) |
| `responses/` · `grades/` | raw captured responses and blind grades |
