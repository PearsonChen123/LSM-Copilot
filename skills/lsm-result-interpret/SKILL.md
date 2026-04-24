---
name: lsm-result-interpret
description: "Result interpretation skill for fluorescence/confocal microscopy. Use when analysis outputs already exist and the user wants literature-grounded discussion of what the numbers mean — not a full manuscript."
version: "0.3.0"
---

# LSM Result Interpret

A focused skill that turns **quantitative analysis outputs** + **retrieved literature/reference evidence** into a **structured interpretation** of what the results mean biologically / physically. It deliberately replaces the old "generate full report" path: no manuscript boilerplate, no fabricated narrative — only evidence-backed discussion.

This skill **consumes**:

1. **Analysis artifacts** produced by `lsm-copilot` (figures, CSV/JSON summaries, parameter logs).
2. **Evidence pack** produced by `ai4s-web-search` (shortlisted references, reference values, methodological citations).
3. **User-supplied experimental context** (sample, channels, treatments, aim).

It **produces**:

- A **structured interpretation block** (markdown) with mandatory sections (see "Output Structure").
- A **caveats checklist**.
- A list of **suggested next analyses / experiments**.

It does **not**:

- Run any computation of its own.
- Perform raw web retrieval by itself; it requests `ai4s-web-search` when literature/reference evidence is missing or thin.
- Draft an end-to-end paper / REPORT.

---

## Trigger Conditions

Activate when:

- The user says things like "help me interpret these results", "what do these numbers mean", "写一下结果解读 / 讨论", "对比文献看看是否合理".
- `lsm-copilot` completes Phase 1 and hands off artifacts for discussion.

Do NOT activate to run new analyses or to write a full manuscript.

---

## Input Contract

Ask **once** if any of the following is missing; otherwise proceed.

```yaml
analysis_artifacts:
  summary:      "<path to summary CSV/JSON, or inline key stats>"
  figures:      ["<path 1>", "<path 2>", "..."]
  parameters:   "<path/log of analysis parameters, or inline>"
  units:        "µm | µm² | µm³ | AU | ..."

experimental_context:
  sample:       "<e.g. mouse cortical slice, HeLa, polymer film>"
  channels:     {"ch1": "...", "ch2": "...", "...": "..."}
  treatments:   ["<e.g. CryoChem, PFA 4%, CLARITY>"]
  aim:          "<scientific question being asked>"
  comparators:  ["<optional: control conditions or replicate counts>"]

evidence_pack:
  # Either: the JSON block returned by ai4s-web-search,
  # OR: a note requesting that this skill invoke ai4s-web-search first.
```

If `evidence_pack` is absent or insufficient and the interpretation requires grounding (e.g., comparing to reference values, naming a technique, citing a method, judging whether a value is plausible), **request `ai4s-web-search` first** before writing the interpretation.

---

## Workflow (Skill Flow)

```
lsm-copilot  ──►  analysis artifacts + method evidence
                       │
ai4s-web-search ──►    │    reference values / literature evidence
                       ▼
               lsm-result-interpret  ──►  structured interpretation
```

### 0. User-feedback correction loop

Use this loop whenever the user says the interpretation, biological claim, evidence alignment, caveat, citation, or conclusion is wrong, or gives feedback like "不对 / 有错误 / 解释错了 / 文献不相关".

1. **Ask for the specific error first.** If the feedback is vague, ask one concise question: which sentence, claim, table row, citation, assumption, or missing context is wrong?
2. **Classify the issue.** Use one or more classes: `artifact_misread`, `wrong_context`, `unsupported_claim`, `bad_citation`, `overclaim`, `missed_caveat`, `wrong_comparator`, `needs_new_analysis`.
3. **Reflect before revising.** State which assumption caused the incorrect interpretation and whether the fix needs new evidence, corrected artifacts from `lsm-copilot`, or only a rewritten conclusion.
4. **Re-ground if needed.** If the correction affects literature/reference claims, request `ai4s-web-search` before revising.
5. **Produce a corrected interpretation.** Include a short "Correction applied" note before the normal output structure, listing the changed claims and any remaining uncertainty.

Do not silently patch a conclusion while keeping the same evidence alignment if the user's correction changes the biological or methodological basis.

### 1. Intake & sanity check

Read artifacts and confirm:

- Units are physical (µm, µm³, AU), not pixels.
- Sample / channel mapping is present.
- Figures exist at the given paths (do not fabricate filenames).
- Missing items go in `caveats`, not silently ignored.

### 2. Literature/reference search

Before interpreting results, ensure the evidence pack covers:

- Method citations when the method affects interpretation.
- Reference values or reported ranges for comparable samples when making plausibility claims.
- Treatment / preparation effects when discussing preservation, quenching, clearing, fixation, or artifacts.
- Known caveats for the measurement type.

If evidence is missing, request `ai4s-web-search`:

```yaml
purpose: reference_values
goal: "<interpret the analysis outputs for the stated sample/aim>"
domain_descriptors: ["fluorescence microscopy", "<sample>", "<measurement>", "<treatment>"]
constraints: ["peer-reviewed or official docs preferred"]
k: 3
```

For method-specific claims, use `purpose: citation_grounding`.

### 3. Evidence alignment

For each headline number in the analysis, pair it with **zero or more evidence items** from the `evidence_pack`:

- **Supported**: consistent with a cited value (give URL and brief phrase).
- **Discrepant**: differs from cited value; explain plausible causes (biology, preparation, analysis choice).
- **Ungrounded**: no citation available; mark `"to our knowledge"` rather than fabricating one.

### 4. Compose interpretation

Follow the **Output Structure** below. Keep it short; interpretation, not exposition.

### 5. Produce next steps

List 2–5 **specific, actionable** follow-ups (e.g. "acquire a paired control fixed with PFA 4%", "run object-based colocalization on ch2 × ch3"). Avoid generic suggestions.

---

## Output Structure

Always emit these sections, in order, as markdown:

```markdown
## Interpretation

### 1. Headline findings
- 2–4 bullets; each bullet ties a measured number to a biological/physical statement.

### 2. Evidence alignment
| Measurement | Our value | Literature / reference | Agreement | Source |
|-------------|-----------|------------------------|-----------|--------|
| ...         | ...       | ...                    | supported / discrepant / ungrounded | <url or "none"> |

### 3. Likely meaning
- Short paragraph linking findings to the user's stated `aim`.
- If evidence is thin, say so.

### 4. Caveats
- Analysis assumptions (thresholds, anisotropy, channel bleed-through, sample size).
- Data limitations (single sample, no control, 2D-only or MIP artefacts).

### 5. Suggested next steps
- Bulleted, specific, prioritized.

### 6. Evidence used
- Bulleted list of the evidence_pack URLs actually cited above.
```

No other sections. No "Abstract", no "Title", no "Acquisition Parameters" table — those belong to a report skill, which we deliberately do not provide.

---

## Tone and Standards

- **Claims must be grounded**. Every comparative statement links to either (a) a cited URL from the evidence pack or (b) explicit wording `"to our knowledge"`.
- **Search before comparison**. Do not compare results with literature, reference ranges, or expected biology until `ai4s-web-search` has supplied relevant evidence or the user has explicitly disabled network use.
- **No manuscript boilerplate**. Do not produce "Background / Methods / Results / Discussion" as a full narrative.
- **Units always physical**. Reject interpretation written in pixels.
- **Honor the user's language**. If the user writes in Chinese, respond in Chinese; the section headers above may be localized, but keep the same structure.
- **Length**: aim for 250–500 words of prose total; tables and bullets in addition.

---

## Anti-Patterns

- Do NOT invent citations when `evidence_pack` is empty or thin — request a search round instead.
- Do NOT hide disagreements between measurement and literature; surface them as `discrepant`.
- Do NOT expand into a full paper draft; that is out of scope.
- Do NOT rerun analysis here; hand back to `lsm-copilot` if new numbers are needed.
- Do NOT over-claim biological significance from a single sample.
- Do NOT dismiss user correction feedback; ask what is specifically wrong and revise the reasoning path before rewriting.
