# Artifact Contract

## Purpose

Every analysis run must preserve the intermediate reasoning and data products, not only final figures. This makes the run auditable, reproducible, and easier to hand off to `lsm-result-interpret`.

Use a stable run directory:

```text
output/<run_id>/
```

Choose `<run_id>` from the task and timestamp or user-provided label, e.g. `tl_statistics_analysis`.

---

## Required Stage Artifacts

| Stage | Required artifacts | Purpose |
|-------|--------------------|---------|
| `00_intake` | `00_intake.json`, optional `00_intake.md` | User request, input paths, assumptions, intended outputs |
| `01_file_metadata` | `01_file_inventory.csv`, `01_file_metadata.json`, optional `01_qc_*` figures | File list, dimensions, voxel sizes, intensity ranges, visual QC |
| `02_layout` | `02_layout_detection.json`, optional `02_layout_notes.md` | Layout/routing decisions and ambiguity notes |
| `03_evidence` | `03_method_search_request.json`, `03_evidence_pack.json`, or `03_evidence_gap.md` | Search request, method evidence, skipped-network note |
| `04_pipeline` | `04_pipeline_decision.md`, optional `04_pipeline_decision.json` | Selected pipeline and rejected alternatives |
| `05_extension` | `05_extension_status.json`; if used: `05_extension_plan.md`, `05_extension_verification.json`, `05_extension_smoke_test.txt`, `05_extension_provenance.json` | Extension gate trace |
| `06_intermediate` | `06_intermediate_*` tables/JSON/figures | Derived tables, cleaned data, normalized values, QC plots |
| `07_final` | `07_final_*` tables/figures | User-facing final outputs |
| `08_summary` | `08_summary.json` | Method, parameters, evidence URLs, caveats, artifact manifest |
| `09_followup` | `09_followup_context.json` or `09_followup_context.md` | Experimental context for interpretation handoff |

If a stage is not applicable, still create a small status file explaining why, e.g. `05_extension_status.json`.

---

## Artifact Manifest

`08_summary.json` must include:

```json
{
  "run_id": "",
  "skill": "lsm-copilot",
  "input_paths": [],
  "method": "",
  "units": [],
  "evidence_urls": [],
  "extension": {
    "status": "not_needed|used|failed|skipped"
  },
  "artifacts": [
    {
      "stage": "00_intake",
      "path": "output/<run_id>/00_intake.json",
      "description": "..."
    }
  ],
  "caveats": []
}
```

---

## Naming Rules

- Use stage prefixes so files sort in workflow order.
- Use physical units in filenames or column names when relevant.
- Keep raw inputs unchanged; write cleaned or derived data as new files.
- Save both machine-readable artifacts (`.json`, `.csv`) and human-readable notes (`.md`) when decisions matter.
- For figures, save publication-quality PNGs at 200 dpi or higher unless the task requires a different format.

---

## Anti-Patterns

- Do not overwrite raw data.
- Do not only save the final figure.
- Do not hide failed searches, skipped extension gates, or failed smoke tests.
- Do not omit caveats from `08_summary.json`.
