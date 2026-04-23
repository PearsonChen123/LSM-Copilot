---
name: ai4s-web-search
description: "Generic AI-for-Science web search helper. Use when any AI4S task needs grounded retrieval of methods, libraries, or reference values before choosing tools or interpreting results."
version: "0.1.0"
---

# AI4S Web Search Helper

A **generic retrieval skill** for AI-for-Science workflows. It is invoked by other skills (e.g., `lsm-copilot`, `lsm-result-interpret`) — or directly by the user — whenever a task needs **grounded, current evidence** before committing to a pipeline or before interpreting numbers.

This skill does **not** perform any image / data analysis. It only:

1. **Builds focused queries** from the caller's **goal + data / domain descriptors**.
2. **Executes web search** (the agent's built-in web tool).
3. **Produces a structured evidence pack** that downstream skills can consume.

---

## Trigger Conditions

Activate when the caller (skill or user) needs to:

- Discover **candidate methods / libraries / models** for a defined task.
- Retrieve **published reference values** (e.g., typical sizes, densities, concentrations).
- Verify **API / installation / license** facts for a named tool.
- Ground a claim with a **paper or docs citation** before writing it down.

Do **not** use this skill for long-form writing, for running any computation, or for paraphrasing previously cached knowledge that does not need verification.

---

## Input Contract (what the caller should provide)

Prefer a short **intent block**; missing fields are filled by asking the caller once.

```yaml
purpose:            method_discovery | reference_values | tool_verification | citation_grounding
goal:               "<what the downstream task is trying to do, one sentence>"
domain_descriptors: ["<free-form tags, e.g. fluorescence microscopy, ZCYX stack, GFP>"]
constraints:        ["<e.g. open source, Python, no CUDA, license==BSD/MIT>"]
k:                  3            # desired number of shortlisted results (default 3)
language:           en | zh      # query language preference
```

If the caller omits `purpose`, infer it from the goal (e.g. asking "which library to use" → `method_discovery`).

---

## Workflow

### 1. Clarify (only if critical fields are missing)

Ask **one** concise question covering all missing critical fields. Never loop indefinitely — after at most one clarification, proceed with best effort and mark the evidence pack with `assumed_fields`.

### 2. Build queries

Combine `goal` + `domain_descriptors` + `constraints` into **2–4 focused queries**. Rules of thumb:

- Put **specific tokens** (tool name, modality, format, unit) before generic ones.
- Include a **recency marker** only when the field moves fast (e.g., DL segmentation): `"2025"` / `"2026"` / `"latest"`.
- For reference values, include **units** in the query (`"µm"`, `"per mm³"`, `"fold"`).
- For tool verification, search both the **GitHub repo** and the **docs site** when known.

Log the final queries in the evidence pack (`queries`).

### 3. Execute search

Use the agent's built-in web search tool. Prefer **primary sources** in this order:

1. Peer-reviewed papers / preprints (with venue + year).
2. Official project docs / READMEs.
3. Well-maintained community posts only as **corroboration**, not as sole source.

When results disagree, record the disagreement explicitly rather than picking a side silently.

### 4. Shortlist & annotate

Return **up to `k`** items. For each item record:

- `title`
- `url`
- `source_type`: `paper | docs | repo | blog | other`
- `year` (if available)
- `license` (for tools/repos; `unknown` allowed)
- `why_relevant` (≤ 30 words; ties item back to the goal)
- `caveats` (≤ 30 words; recency, scope mismatch, reproducibility concerns)

Deduplicate by project/DOI. If nothing credible was found, return an empty list and set `confidence: "low"` with a short `notes` explanation.

### 5. Produce the evidence pack

Emit a single structured block the caller can machine-parse. See `templates/evidence_pack.md`.

---

## Output Contract

Always return at least the JSON block below. Markdown prose is optional and should summarize — never replace — the JSON.

```json
{
  "purpose": "method_discovery",
  "goal": "...",
  "queries": ["...", "..."],
  "results": [
    {
      "title": "...",
      "url": "...",
      "source_type": "paper",
      "year": 2024,
      "license": "unknown",
      "why_relevant": "...",
      "caveats": "..."
    }
  ],
  "assumed_fields": [],
  "confidence": "medium",
  "notes": ""
}
```

Downstream skills may read `results[*]` as evidence and cite `url` verbatim.

---

## Anti-Patterns

- Do NOT fabricate citations, DOIs, or author names.
- Do NOT silently rewrite the caller's `goal`; if ambiguous, ask once or record as `assumed_fields`.
- Do NOT extend to writing discussion, interpreting results, or running analysis — hand back to the caller.
- Do NOT exceed `k` shortlisted items; the caller can request another round.
- Do NOT treat a single blog post as a primary source for method choice.
