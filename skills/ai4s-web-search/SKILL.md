---
name: ai4s-web-search
description: "Generic AI-for-Science web search helper. Use when any AI4S task needs grounded retrieval of methods, libraries, install facts, licenses, APIs, or reference values."
version: "0.3.0"
---

# AI4S Web Search Helper

A **generic retrieval skill** for AI-for-Science workflows. It is invoked by other skills (e.g., `lsm-copilot`, `lsm-result-interpret`) — or directly by the user — whenever a task needs **grounded, current evidence** before committing to a pipeline, extending a workflow, installing a tool, or interpreting numbers.

This skill does **not** perform any image / data analysis. It only:

1. **Builds focused queries** from the caller's **goal + data / domain descriptors**.
2. **Executes web search** (the agent's built-in web tool).
3. **Produces a structured evidence pack** that downstream skills can consume.

---

## Trigger Conditions

Activate when the caller (skill or user) needs to:

- Discover **candidate methods / libraries / models** for a defined task.
- Discover **candidate extensions** when a downstream skill lacks a capability.
- Retrieve **published reference values** (e.g., typical sizes, densities, concentrations).
- Verify **API / installation / license** facts for a named tool.
- Ground a claim with a **paper or docs citation** before writing it down.

Do **not** use this skill for long-form writing, for running any computation, or for paraphrasing previously cached knowledge that does not need verification.

---

## Input Contract (what the caller should provide)

Prefer a short **intent block**; missing fields are filled by asking the caller once.

```yaml
purpose:            method_discovery | extension_discovery | reference_values | tool_verification | citation_grounding
goal:               "<what the downstream task is trying to do, one sentence>"
domain_descriptors: ["<free-form tags, e.g. fluorescence microscopy, ZCYX stack, GFP>"]
constraints:        ["<e.g. open source, Python, no CUDA, license==BSD/MIT>"]
k:                  3            # desired number of shortlisted results (default 3)
language:           en | zh      # query language preference
```

If the caller omits `purpose`, infer it from the goal (e.g. asking "which library to use" → `method_discovery`; asking "can we install/integrate a tool for X" → `extension_discovery`).

---

## Workflow

### 0. User-feedback correction loop

Use this loop whenever the user says the search/evidence is wrong, incomplete, irrelevant, outdated, or "不对 / 有错误 / 不是这个".

1. **Ask for the specific error first.** If the feedback is vague, ask one concise question: which result, query, citation, license/install fact, or missing method is wrong?
2. **Classify the issue.** Mark it as `wrong_scope`, `missing_source`, `outdated_source`, `low_quality_source`, `incorrect_license_or_install`, `bad_query`, or `contradictory_evidence`.
3. **Reflect before re-searching.** State what assumption caused the error and how the query/evidence criteria will change.
4. **Run a corrected search.** Build revised queries from the user's correction; prefer primary sources and explicitly exclude the prior failure mode.
5. **Emit a corrected evidence pack.** Include a `correction` block with the user feedback, issue class, changed queries, superseded result IDs/URLs, and remaining uncertainty.

Do not defend the previous pack when the user reports an error. Treat feedback as new evidence and revise the retrieval plan.

### 1. Clarify (only if critical fields are missing)

Ask **one** concise question covering all missing critical fields. Never loop indefinitely — after at most one clarification, proceed with best effort and mark the evidence pack with `assumed_fields`.

### 2. Build queries

Combine `goal` + `domain_descriptors` + `constraints` into **2–4 focused queries**. Rules of thumb:

- Put **specific tokens** (tool name, modality, format, unit) before generic ones.
- Include a **recency marker** only when the field moves fast (e.g., DL segmentation): `"2025"` / `"2026"` / `"latest"`.
- For reference values, include **units** in the query (`"µm"`, `"per mm³"`, `"fold"`).
- For extension discovery, include terms for install, API examples, license, and maintenance status.
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

For `extension_discovery` or `tool_verification`, also record when available:

- `install`: package manager command or official install URL.
- `api_entrypoint`: minimal import/function/CLI entry point.
- `maintenance`: active | limited | archived | unknown.
- `integration_risk`: low | medium | high.

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
  "correction": null,
  "queries": ["...", "..."],
  "results": [
    {
      "title": "...",
      "url": "...",
      "source_type": "paper",
      "year": 2024,
      "license": "unknown",
      "install": null,
      "api_entrypoint": null,
      "maintenance": "unknown",
      "integration_risk": "medium",
      "why_relevant": "...",
      "caveats": "..."
    }
  ],
  "assumed_fields": [],
  "confidence": "medium",
  "notes": ""
}
```

Downstream skills may read `results[*]` as evidence and cite `url` verbatim. For extension work, `lsm-copilot` must treat this pack as input to an approval gate, not as permission to install automatically.

When produced after user feedback, set `correction` to:

```json
{
  "user_feedback": "...",
  "issue_class": "wrong_scope",
  "reflection": "Previous query over-weighted generic segmentation and under-weighted confocal LSM droplet data.",
  "changed_queries": ["..."],
  "superseded_urls": ["..."],
  "remaining_uncertainty": "..."
}
```

---

## Anti-Patterns

- Do NOT fabricate citations, DOIs, or author names.
- Do NOT silently rewrite the caller's `goal`; if ambiguous, ask once or record as `assumed_fields`.
- Do NOT extend to writing discussion, interpreting results, or running analysis — hand back to the caller.
- Do NOT install packages, clone repositories, download weights, or execute candidate tools.
- Do NOT exceed `k` shortlisted items; the caller can request another round.
- Do NOT treat a single blog post as a primary source for method choice.
- Do NOT rerun the same query set after user correction without first stating what assumption changed.
