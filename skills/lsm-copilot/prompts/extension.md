# Controlled Extension / Auto-Install Gate

## When to Use

Use this workflow when:

- Built-in tools cannot meet the user's analysis goal.
- `ai4s-web-search` finds a third-party method that is materially better for the data/task.
- The user explicitly asks to add support for a new open-source algorithm, package, or model.

Do not use this workflow for simple parameter tuning or for a method that can be implemented safely with existing dependencies.

---

## Required Inputs

```yaml
capability_gap: "<what the current tools cannot do>"
success_criteria: "<observable result, artifact, or metric>"
data_context:
  layout: "<2D | 3D | multichannel | time series | mixed>"
  modality: "<confocal, fluorescence, LSM, CZI, TIFF, MRC, ...>"
  constraints: ["open source", "python", "no CUDA", "license allowed", "..."]
evidence_pack: "<from ai4s-web-search; purpose=extension_discovery or tool_verification>"
```

If the evidence pack is missing, request `ai4s-web-search` first.

---

## Extension Evidence Request

```yaml
purpose: extension_discovery
goal: "<new capability needed by the analysis>"
domain_descriptors: ["fluorescence microscopy", "<layout>", "<task>", "<file format>"]
constraints: ["open source", "python", "<runtime/license constraints>"]
k: 3
```

For a named candidate, request:

```yaml
purpose: tool_verification
goal: "Verify install, license, API, and maintenance status for <tool> before integration"
domain_descriptors: ["<tool>", "GitHub", "documentation", "Python API"]
constraints: ["license", "install command", "minimal example", "latest supported Python"]
k: 3
```

---

## Extension Plan Template

Before installing or cloning anything, present a concise plan:

```yaml
selected_tool:
  name: ""
  source_url: ""
  docs_url: ""
  license: ""
  version_or_commit: ""
why_selected: ""
install:
  command: ""
  environment: "<active venv | project env | new env>"
  expected_downloads: "<none | package wheels | model weights | repo clone>"
integration:
  adapter_path: "tools/extensions/<tool>_adapter.py"
  entrypoint: "<function or CLI this adapter will call>"
  output_contract: "<CSV/JSON/figure paths and columns>"
validation:
  smoke_test: "<import check or tiny sample command>"
  fallback: "<built-in method to use if extension fails>"
risks:
  - "<license, GPU, model weight, memory, reproducibility, API stability>"
```

Ask for explicit user approval after showing this plan. Approval must happen before any install, clone, model download, adapter/tool code addition, or full-data run.

---

## Implementation Rules

- Prefer packages from PyPI/conda with official docs over arbitrary repo scripts.
- Do not write extension adapter code until the user has approved the selected method and extension plan.
- Avoid global installs. Use the active virtual environment or a documented project environment.
- Pin versions when reproducibility matters.
- Put glue code in `tools/extensions/`; keep adapters thin and deterministic.
- Do not vendor large source trees or model weights into git.
- If a source clone is needed for inspection, put it under `third_party/<tool>/` and make sure it is gitignored when large.
- Record source URL, license, version/commit, install command, and citation note in `third_party/README.md` or the analysis summary JSON.
- Run a smoke test before running the full analysis.

---

## Stop Conditions

Stop and ask the user before proceeding when:

- The tool has an unclear, restrictive, or missing license.
- Installation requires GPU/CUDA, compiler toolchains, Java, Docker, or large downloads.
- The package wants to execute unknown setup scripts from a repo rather than a normal package manager.
- The candidate changes scientific interpretation rather than only computation.
- The smoke test fails.

---

## Final Artifact Requirements

If an extension was used, the analysis summary JSON must include:

```json
{
  "extension": {
    "name": "",
    "source_url": "",
    "docs_url": "",
    "license": "",
    "version_or_commit": "",
    "install_command": "",
    "adapter_path": "",
    "smoke_test": "",
    "status": "used|failed|skipped",
    "caveats": []
  }
}
```
