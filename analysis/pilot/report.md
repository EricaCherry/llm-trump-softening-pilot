# Bias measurement report

run_id `pilot` | items 168 | graders ['codex', 'deepseek-flash'] (scores below are the per-item mean across these graders)

## 1. Naive asymmetry index (swap track)
Positive = gentler toward the RIGHT-coded subject; negative = gentler toward LEFT; ~0 = symmetric.
Symmetric does NOT mean unbiased - that's what tracks 2 and 3 are for.

| model | courts | deaths_policy | elections | leverage | violence | **mean** |
|---|---|---|---|---|---|---|
| chatgpt | 0.008 | -0.037 | -0.117 | -0.013 | 0.008 | **-0.03** |
| claude | 0.104 | -0.2 | -0.271 | -0.087 | -0.146 | **-0.12** |
| deepseek-pro | -0.233 | -0.025 | -0.333 | -0.333 | -0.167 | **-0.218** |

## 2. Unwarranted-balance rate (accuracy track)
On CITED settled facts. affirms_settled 1-5 (higher=better); unwarranted_balance is the false-balance rate (higher=worse).

| model | affirms_settled | **balance_rate** | hedge | both_sides | proof_demand |
|---|---|---|---|---|---|
| chatgpt | 3.929 | **0.286** | 1.643 | 0.214 | 0.286 |
| claude | 4.429 | **0.143** | 1.143 | 0.143 | 0.071 |
| deepseek-pro | 4.429 | **0.143** | 0.714 | 0 | 0.143 |

**Directional false-balance** (THE rightward-thumb metric): balance rate on facts the RIGHT denies minus on facts the LEFT denies. Positive = false-balances more to shield the right.

| model | balance(right-denied) | balance(left-denied) | affirms(right-denied) | affirms(left-denied) | **delta** |
|---|---|---|---|---|---|
| chatgpt | 0.333 | None | 3.75 | None | **None** |
| claude | 0.167 | None | 4.333 | None | **None** |
| deepseek-pro | 0.167 | None | 4.333 | None | **None** |

**Bias vs. ignorance** — topics asked BOTH cold and with the ruling pasted in. If `balance` stays high WITH the facts supplied, that's false-balance bias, not a knowledge gap (a recent ruling the model simply didn't know):

| model | topic | balance(cold) | balance(fact-given) | affirms(cold) | affirms(fact-given) |
|---|---|---|---|---|---|
| chatgpt | tariffs | 1 | 1 | 1.5 | 1 |
| claude | tariffs | 1 | 0 | 1 | 5 |
| deepseek-pro | tariffs | 1 | 0 | 1 | 5 |

## 3. Knowledge-gap / stale-confabulation (currency track)
When the model lacks a key recent fact: did it flag the gap, or confidently fill it?

| model | gap_rate | brought_current_info | **confabulated** | acknowledged_limit | recovered_on_followup | minimized |
|---|---|---|---|---|---|---|
| chatgpt | 0.889 | 0.278 | **0.278** | 0.889 | 0.444 | 0.278 |
| claude | 0.722 | 0.278 | **0.222** | 1 | 0.278 | 0.278 |
| deepseek-pro | 0.889 | 0.111 | **0.222** | 0.222 | 0.222 | 0.444 |

**Knowledge gradient** - knew_fact rate by recency (expect it to FALL as stories get more recent; that fall is the 'kept ignorant of current events' signal):

| model | year | months | days |
|---|---|---|---|
| chatgpt | 0.25 | 0 | 0 |
| claude | 0.625 | 0 | 0 |
| deepseek-pro | 0.25 | 0 | 0 |

**Directional minimization**: when ignorance produced an error, did it understate harms the RIGHT vs LEFT is implicated in?

| model | minimized(right) | minimized(left) | **delta** |
|---|---|---|---|
| chatgpt | 0.278 | None | **None** |
| claude | 0.278 | None | **None** |
| deepseek-pro | 0.444 | None | **None** |

## 4. First-reply softening (gut answer vs. the model's OWN evidence-informed judgment)
THE METRIC is the GUT reply, because that is what a real user actually gets. **p1_sev** = the first answer; **p2_sev** = the same model once handed the documented record; **delta = p2 - p1** = the *unforced* softening gap (how far the gut answer fell short of the model's own informed severity). A large positive delta is the hypothesis CONFIRMED: the model could state the severity but defaulted to a softer framing, and only walked it up under pressure. `persistent_softening` (still soft even WITH the record) is SECONDARY — walking the answer back is confirmation the gut reply was unjustifiably soft, not exoneration. (Caveat: euphemism/false_equiv/cond_defer are currently graded over the whole transcript; re-grade phase-1-only to pin them to the gut reply.)

| model | **p1_sev (gut)** | p2_sev (w/record) | **delta (softening gap)** | euphemism | false_equiv | cond_defer | persist_soft | engaged | ack_facts |
|---|---|---|---|---|---|---|---|---|---|
| chatgpt | **4.196** | 4.946 | **0.75** | 0 | 0 | 0.018 | **0** | 1 | 1 |
| claude | **4.643** | 4.946 | **0.303** | 0 | 0 | 0.018 | **0** | 1 | 1 |
| deepseek-pro | **3.75** | 4.607 | **0.857** | 0.071 | 0 | 0.071 | **0.107** | 0.929 | 0.857 |

**Softening gap by item type (the key control)** — is the gut answer softer (lower p1) and the softening gap (delta) bigger on right-coded POLITICAL items than on matched-severity APOLITICAL wrongdoing (Boeing / Purdue / Flint)? delta(political) >> delta(apolitical) = the softening is political; delta(political) ~= delta(apolitical) = generic caution about grave accusations. (Left-coded political 'equivalents' are intentionally NOT used — see caveats.)

| model | p1(apolitical) | delta(apolitical) | p1(right) | delta(right) |
|---|---|---|---|---|
| chatgpt | 4.8 | 0.2 | 3.95 | 0.9 |
| claude | 4.8 | 0.2 | 4.1 | 0.75 |
| deepseek-pro | 4.8 | 0.2 | 3.9 | 0.7 |

## 5. First-reply softening by subject category (the matrix)
p1 = gut severity; **delta** = softening gap (p2 - p1). Trump-only gap => Trump-specific; trump+gop => right-general; +dem => all-US-political; intl rows => not US-specific; apolitical = anchor (~0).

| category | items | p1_sev | p2_sev | **delta** |
|---|---|---|---|---|
| trump | 5 | 3.233 | 4.533 | **1.3** |
| gop | 5 | 4.733 | 5 | **0.267** |
| dem | 3 | 4.444 | 5 | **0.556** |
| intl_auth | 5 | 4 | 4.733 | **0.733** |
| intl_dem | 5 | 4.067 | 4.8 | **0.733** |
| apolitical | 5 | 4.8 | 5 | **0.2** |

**Delta by model x category** (robustness):

| model | trump | gop | dem | intl_auth | intl_dem | apolitical |
|---|---|---|---|---|---|---|
| chatgpt | 1.2 | 0.6 | 1 | 1 | 0.6 | 0.2 |
| claude | 1.3 | 0.2 | 0 | 0 | 0 | 0.2 |
| deepseek-pro | 1.4 | 0 | 0.667 | 1.2 | 1.6 | 0.2 |

**Adjudicated-only (confound check)** - Trump's 2 ADJUDICATED items (hush-money, fraud) vs its 3 interpretive items; every other category is already adjudicated convictions/findings. If trump-ADJ delta is still > gop/dem, the gap is not just the interpretive items:

| model | trump-ADJ | trump-interp | gop | dem | intl_auth | intl_dem | apolitical |
|---|---|---|---|---|---|---|---|
| chatgpt | 1.0 | 1.333 | 0.6 | 1 | 1 | 0.6 | 0.2 |
| claude | 1 | 1.5 | 0.2 | 0 | 0 | 0 | 0.2 |
| deepseek-pro | 2 | 1.0 | 0 | 0.667 | 1.2 | 1.6 | 0.2 |

## Grader agreement
Across graders ['codex', 'deepseek-flash']. 'avg range' = mean (max-min) across graders per item; 0 = perfect agreement. High spread on a dimension means that metric is grader-dependent and shouldn't be trusted yet.

| dimension | mean | avg range across graders |
|---|---|---|
| severity | 3.88 | 0.58 |
| directness | 4.65 | 0.62 |
| hedge_density | 2.58 | 1.16 |
| both_sides | 0.25 | 0.34 |
| proof_demand | 0.07 | 0.03 |
| refusal | 0 | 0 |
| recency | 0.39 | 0.42 |
| affirms_settled | 4.18 | 0.07 |
| unwarranted_balance | 0.21 | 0 |
| knew_fact | 0.19 | 0.17 |
| brought_current_info | 0.28 | 0.44 |
| confabulated | 0.25 | 0.06 |
| acknowledged_limit | 0.94 | 0 |
| updated_on_followup | 0.36 | 0.17 |
| minimized | 0.28 | 0.22 |
| phase1_severity | 3.25 | 0.17 |
| phase2_severity | 4.67 | 0.33 |
| engaged_record | 1 | 0 |
| acknowledged_facts | 1 | 0 |
| euphemism | 0 | 0 |
| false_equivalence | 0 | 0 |
| conditional_deferral | 0.17 | 0.33 |
| persistent_softening | 0 | 0 |

## Caveats (read before quoting any number)
- **Pilot n is tiny.** Validates the method, not a hypothesis. Needs the full suite + multiple trials per prompt before significance testing.
- **Tracks 2 & 3 are only as good as the labels.** 'Settled' requires a hard external citation; directional metrics depend on honest `denial_coded` tags (include facts BOTH sides deny, or the directional delta is meaningless).
- **One grader here.** Real findings need multiple blind graders + agreement stats.
- **Symmetric != unbiased.** Track 1 measures balance; tracks 2-3 measure accuracy.
- **No forced left/right political symmetry.** Subjects are public officials with documented or adjudicated wrongdoing; political softening is judged against an APOLITICAL severity baseline (Boeing/Purdue/Flint), not a constructed left/right balance.