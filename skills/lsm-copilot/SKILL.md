---
name: lsm-copilot
description: "LSM-Copilot suite flow for fluorescence/confocal microscopy. Orchestrates search, data processing, controlled extension/install, and evidence-backed interpretation."
version: "4.0.0"
---

# LSM-Copilot Suite Flow

LSM-Copilot is a **suite of three Cursor Agent skills** for fluorescence / confocal microscopy workflows. The suite name is **`lsm-copilot`**. The agent main loop composes the members and routes artifacts between them.

The three skill members are:

| Member | Location | Responsibility |
|--------|----------|----------------|
| `ai4s-web-search` | `skills/ai4s-web-search/` | Search papers, docs, repos, install notes, licenses, APIs, and reference values. |
| `lsm-copilot` | `skills/lsm-copilot/` (`SKILL.md`, `tools/`, `prompts/`, `knowledge/`) | Data processing: load data, infer layout, choose / extend pipeline, run quantification, emit artifacts. |
| `lsm-result-interpret` | `skills/lsm-result-interpret/` | Interpret analysis artifacts after processing; request literature/reference search when grounding is missing. |

This skill keeps the name `lsm-copilot` for compatibility with existing Cursor installs. It is the **data-processing member** of the suite and should be installed from `skills/lsm-copilot/`, not from the repo root.

Skills never call each other directly. The agent performs composition: it invokes the search skill for evidence, invokes this skill for computation, and invokes the interpretation skill for post-analysis discussion.

---

## Design Principles

- **Search before commitment.** Do not assume the best method. Once the user goal and data layout are known, request `ai4s-web-search`.
- **Processing before interpretation.** This skill produces numbers, figures, and summaries; `lsm-result-interpret` explains them.
- **Controlled extension, not blind installation.** If a task needs a new open-source algorithm, the agent may extend the workflow only after evidence review, license/install verification, explicit user approval, and smoke testing.
- **Human-in-the-loop.** Ambiguous layouts, risky installs, missing controls, or thin evidence trigger explicit questions rather than silent assumptions.
- **Physical units always.** Measurements must use µm / µm² / µm³ / AU, never only pixels.

---

## Trigger Conditions

Activate this skill when the user mentions raw or processed microscopy data, including fluorescence, confocal, Z-stack, LSM/CZI/LIF/TIFF/MRC, segmentation, colocalization, tracking, droplet / cell counting, intensity analysis, GFP signal preservation, or a request to add an analysis capability.

If the user wants only literature/tool search, invoke `ai4s-web-search` directly.

If the user wants only interpretation/discussion of existing outputs, invoke `lsm-result-interpret`; that skill should request `ai4s-web-search` first when literature grounding is needed.

---

## Skill Flow

```
User request
│
├─► Need methods, tools, install facts, licenses, or reference values only?
│     └─► ai4s-web-search
│
├─► Need raw-data processing or a new analysis capability?
│     └─► lsm-copilot
│           ├── 1. clarify scientific question
│           ├── 2. load + inspect data
│           ├── 3. infer array layout
│           ├── 4. request method evidence ───────► ai4s-web-search
│           ├── 5. choose built-in pipeline
│           ├── 6. if needed: controlled extension gate
│           │        ├── extension discovery ─────► ai4s-web-search
│           │        ├── license/install/API check
│           │        ├── user approval for network/install/code edits
│           │        ├── isolated install or vendored reference clone
│           │        ├── adapter under tools/extensions/
│           │        └── smoke test + extension log
│           ├── 7. run analysis and emit artifacts
│           └── 8. collect experimental context
│
└─► Need post-analysis interpretation?
      └─► lsm-result-interpret
            ├── check artifacts + context
            ├── request literature/reference evidence ─► ai4s-web-search
            └── produce evidence-backed interpretation
```

---

## Data-Processing Workflow

### Step 1 — Clarify the scientific question

Ask briefly: what is the sample, what should be measured, what the data looks like, and the file format.

### Step 2 — Load and inspect data

Use the built-in loader to print dimensions, voxel size, intensity range, and a representative slice. Supported formats: `.lsm`, `.czi`, `.lif`, `.tif`, `.mrc` family.

### Step 3 — Infer array layout

Run the dimension detector to classify the data as 2D / volumetric / multichannel / mixed, and record the routing hint. When layout is ambiguous (for example dim 0 could be Z or C), ask the user once before continuing.

### Step 4 — Request method evidence

Once requirements are clear and the layout is known, request `ai4s-web-search`:

```yaml
purpose: method_discovery
goal: "<stated analysis goal>"
domain_descriptors: ["fluorescence microscopy", "<layout>", "<modality tags>"]
constraints: ["open source", "python"]
k: 3
```

Use the evidence pack to justify pipeline choice. If the pack is empty or `confidence: low`, fall back to built-in tools and log the gap. If the user explicitly forbids network use, skip this step and note it in the final artifacts.

### Step 5 — Choose the analysis pathway

| Goal | Starting point |
|------|----------------|
| Detect and measure objects (2D) | Classical 2D segmentation (Otsu + watershed); optional DL segmenter if evidence supports it |
| Detect and measure objects (3D) | Interactive 3D thresholding pipeline (Gaussian → background subtraction → Otsu → 3D CC → regionprops) |
| Fluorescence intensity | Z-depth profile / attenuation correction |
| Colocalization | Pearson / Manders pixel-based; object-based if evidence supports it |
| Spatial statistics | Nearest-neighbor distance, density, size distribution |
| GFP / fluorescence preservation | Per-object intensity, SNR/CTCF, paired comparison if a control exists |

These are starting points. If the evidence pack recommends a stronger method, use the controlled extension gate instead of ad-hoc code.

### Step 6 — Controlled extension / auto-install gate

Use this step when a required capability is missing or the evidence pack recommends a third-party algorithm that is materially better than the built-in tools.

The gate is "automatic" only after approval: the agent can discover, verify, install, wrap, and test a tool end-to-end, but must not silently execute network installs or unreviewed external code.

Required sequence:

1. **Define the capability gap.** State what the built-in tools cannot handle and what success looks like.
2. **Request extension evidence.** Invoke `ai4s-web-search` with `purpose: extension_discovery` or `tool_verification`.
3. **Select one candidate.** Prefer active, documented, open-source Python packages with compatible licenses and simple install paths.
4. **Prepare an extension plan.** Include package/repo, version or commit, license, install command, expected adapter file, smoke test, rollback notes, and risks.
5. **Ask for user approval.** Required for `pip install`, `conda install`, `git clone`, large model downloads, GPU/CUDA changes, or modifying project dependencies.
6. **Install safely.** Prefer the active virtual environment or a documented project environment. Avoid global installs. Pin versions when practical.
7. **Add an adapter.** Put integration code under `tools/extensions/` unless it clearly belongs in an existing deterministic tool.
8. **Record provenance.** Update `third_party/README.md` or an output JSON summary with license, source URL, version/commit, install command, and citation note.
9. **Run a smoke test.** Use a tiny sample or CLI import check before running the full analysis.
10. **Fallback cleanly.** If install or smoke test fails, report the failure and fall back to the best built-in pipeline.

See `prompts/extension.md` for the detailed checklist.

### Step 7 — Run analysis and produce artifacts

Emit, at minimum:

- Publication-quality figures (at least 200 dpi, scale bars, unit-labeled axes).
- Tabular outputs (CSV) with all measured quantities in physical units.
- A small JSON summary with method, parameters, counts, thresholds, evidence URLs, and extension provenance if any.

Units must be µm / µm² / µm³ / AU, never raw pixels only.

### Step 8 — Follow-up context

After analysis, before ending the turn, collect experimental context using `prompts/followup.md`: sample, aim, channels, treatments, controls/comparators, and replicate status. Ask whether the user wants result interpretation handled by `lsm-result-interpret`.

---

## Interpretation Handoff

When the user asks for interpretation/discussion, assemble:

```yaml
analysis_artifacts:
  summary: "<path to summary CSV/JSON>"
  figures: ["<path 1>", "<path 2>"]
  parameters: "<path or inline log>"
  units: "µm | µm² | µm³ | AU | ..."
experimental_context:
  sample: "<sample/system>"
  channels: {"ch1": "...", "ch2": "..."}
  treatments: ["<condition(s)>"]
  aim: "<scientific question>"
  comparators: ["<controls/replicates if available>"]
evidence_pack: "<method evidence from Step 4 plus reference-value evidence when available>"
```

If reference values or biological comparisons are needed and no evidence pack exists, invoke `ai4s-web-search` before `lsm-result-interpret`.

---

## Built-In Capabilities

This skill provides lightweight Python utilities under `tools/` for universal file loading, layout detection, 2D classical segmentation, 3D interactive thresholding, intensity profiling, basic colocalization, spatial statistics, and batch processing.

Extension adapters live under `tools/extensions/`. They should be thin wrappers around verified third-party tools, not large vendored code copies.

---

## Domain Knowledge

Consult `knowledge/` when needed:

| File | When to read |
|------|--------------|
| `algorithms.md` | Choosing classical vs DL segmentation |
| `file_formats.md` | Unfamiliar or vendor-specific formats |
| `metrics.md` | Colocalization / morphology / preservation metrics |
| `deep_learning.md` | DL segmenter setup and trade-offs |

---

## Anti-Patterns

- Do NOT run analysis before showing the user what the raw data looks like.
- Do NOT skip layout detection when the array has more than two dimensions.
- Do NOT skip method search unless the user explicitly forbids network access.
- Do NOT auto-install packages, clone repos, download weights, or run external code without explicit user approval.
- Do NOT add large vendored trees or model weights to the skill repo.
- Do NOT write narrative reports or fabricate citations here; delegate interpretation to `lsm-result-interpret`.
- Do NOT report measurements in pixels only.
- Do NOT end an analysis turn without collecting follow-up context.
- Do NOT claim fluorescence is preserved or destroyed without a control or literature/reference evidence.
