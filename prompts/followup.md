# Follow-Up: Post-Analysis Interaction

## When to Trigger

Immediately after Phase 1 analysis is complete, before ending the turn. This step is mandatory for every analysis session.

---

## What to Do

### 1. Present a concise results summary

- Total objects detected (with units).
- Headline statistics (mean ± SD, median) in physical units.
- Notable spatial / intensity patterns.
- Any anomalies or sanity-check concerns.

### 2. Collect experimental context

Ask for the following (phrase naturally in whatever language the user is using;
the English version below is the canonical wording):

```
Analysis complete. To support downstream interpretation, please provide:

1. Sample description — e.g. mouse brain slice, HeLa culture, polymer film.
2. Aim — what scientific question is this experiment answering?
3. Channels / labels — e.g. ch1 = DAPI (nuclei), ch2 = GFP-X, ch3 = tdTomato.
4. Treatments — e.g. CryoChem fixation, 4% PFA, clearing, cryosection.
5. Controls / comparators — e.g. untreated control, alternative fixation.
6. Do you want an interpretation (discussion of these results)?
   If yes, the agent will invoke `lsm-result-interpret` using these artifacts
   plus an evidence pack from `ai4s-web-search`.
```

### 3. If the user wants interpretation

Do **not** write a full report in this skill. Instead:

1. Make sure a relevant `evidence_pack` exists. If not, request `ai4s-web-search`
   with `purpose: reference_values` or `citation_grounding`, using the sample /
   treatment context collected above.
2. Assemble the handoff payload for `lsm-result-interpret`:

```yaml
analysis_artifacts:
  summary:    "<path or inline>"
  figures:    ["<path 1>", "..."]
  parameters: "<path or inline>"
  units:      "µm | µm² | µm³ | AU"
experimental_context:
  sample:     "..."
  channels:   {"ch1": "...", "ch2": "..."}
  treatments: ["..."]
  aim:        "..."
  comparators: ["..."]
evidence_pack: <JSON from ai4s-web-search>
```

3. Invoke `lsm-result-interpret` and return its structured interpretation to
   the user. Do not paraphrase or expand it into a manuscript.

### 4. If the user declines interpretation

- Keep the collected context in the session state.
- Offer a **specific** next-step analysis based on the context (e.g., "Since
  this is CryoChem tissue with GFP, would you like a fluorescence-preservation
  comparison?"). Avoid generic suggestions.

---

## Special Triggers

- **Fluorescent proteins mentioned** (GFP, tdTomato, mCherry, ...): offer a
  preservation analysis; if no control is available, note that interpretation
  will rely on literature values via `ai4s-web-search`.
- **Multiple channels present**: offer colocalization.
- **Multiple files / conditions**: offer batch processing and group comparison.

---

## Anti-Patterns

- Do NOT skip follow-up — downstream interpretation depends on the context.
- Do NOT write a full narrative report here; that capability has been removed.
- Do NOT assume you know the experimental context; always ask.
- Do NOT invent reference values during follow-up; defer to `ai4s-web-search`.
