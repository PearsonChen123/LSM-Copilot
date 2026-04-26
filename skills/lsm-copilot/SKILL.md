---
name: lsm-copilot
description: "LSM-Copilot suite flow for fluorescence/confocal microscopy. Orchestrates search, data processing, controlled extension/install, and evidence-backed interpretation."
version: "4.5.0"
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
- **Method approval before implementation.** For a new task, benchmark, or data type where the best method is not already fixed by the user, first search the internet, recommend the most suitable method with evidence, and ask the user to approve the method/use plan before installing packages, writing adapters/tools, or running the full analysis.
- **Human-in-the-loop.** Ambiguous layouts, risky installs, missing controls, or thin evidence trigger explicit questions rather than silent assumptions.
- **Artifacts at every step.** Do not only return final figures. Save intake, layout, evidence, pipeline decisions, QC, intermediate tables, final tables, and interpretation handoff files under the run output directory.
- **Raw images before derived exports.** When raw microscopy files (`.lsm`, `.czi`, `.lif`, `.tif`, `.mrc`) and derived CSV/statistics exports are both present, use the raw image as the primary analysis input. Treat CSV/statistics exports as post hoc benchmarks or comparison references unless the user explicitly asks to analyze tables only.
- **Physical units always.** Measurements must use µm / µm² / µm³ / AU, never only pixels.
- **Correction-aware workflow.** If the user reports an error, pause the normal flow, ask what is specifically wrong, then revise assumptions, parameters, method choice, or outputs based on that feedback.

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
│           ├── 5. recommend method + request user approval
│           ├── 6. choose approved pipeline
│           ├── 7. if needed: controlled extension gate
│           │        ├── extension discovery ─────► ai4s-web-search
│           │        ├── license/install/API check
│           │        ├── user approval for network/install/code edits
│           │        ├── isolated install or vendored reference clone
│           │        ├── adapter under tools/extensions/
│           │        └── smoke test + extension log
│           ├── 8. run analysis and emit artifacts
│           └── 9. collect experimental context
│
└─► Need post-analysis interpretation?
      └─► lsm-result-interpret
            ├── check artifacts + context
            ├── request literature/reference evidence ─► ai4s-web-search
            └── produce evidence-backed interpretation
```

---

## Data-Processing Workflow

### Step 0 — User-feedback correction loop

Use this loop whenever the user says the analysis, threshold, volume, count, figure, file choice, or workflow is wrong, or uses feedback like "不对 / 有错误 / 这个结果不对 / 阈值错了 / 体积算法错了".

1. **Ask for the specific error first.** If feedback is vague, ask one concise question that requests the concrete mismatch: which file/group, which metric or figure, expected behavior/value, and why the current result looks wrong.
2. **Classify the issue.** Use one or more classes: `wrong_input_source`, `layout_error`, `parameter_error`, `algorithm_error`, `unit_or_voxel_error`, `benchmark_mismatch`, `visual_qc_error`, `artifact_missing`, `interpretation_handoff_error`.
3. **Reflect before changing code or rerunning.** Record what assumption likely failed, what evidence supports the correction, and which part of the pipeline must change.
4. **Create a correction run or revision.** Do not silently overwrite prior outputs unless the user asks. Prefer `output/<run_id>_corrected/` or add `correction_id` to the existing run.
5. **Use raw data as primary evidence.** If CSV/statistics exports are involved, use them only to diagnose or benchmark image-derived measurements unless the user explicitly requests table-only analysis.
6. **Rerun only the necessary stages.** Recompute affected stages, regenerate intermediate QC figures/tables, and preserve unchanged artifacts.
7. **Write a correction log.** Save `00_correction_feedback.md` and `08_correction_summary.json` with user feedback, issue class, changed assumptions, changed parameters/code, affected artifacts, before/after metrics, and unresolved risks.

If the user's correction implies a new method or external package is needed, enter Step 6 controlled extension gate before installing or running it.

### Step 1 — Clarify the scientific question

Ask briefly: what is the sample, what should be measured, what the data looks like, and the file format.

Create a run directory before computation:

```text
output/<run_id>/
```

Record the user request, assumptions, input paths, and planned artifacts in `00_intake.json` / `00_intake.md`. See `prompts/artifact_contract.md`.

### Step 2 — Load and inspect data

Use the built-in loader to print dimensions, voxel size, intensity range, and a representative slice. Supported formats: `.lsm`, `.czi`, `.lif`, `.tif`, `.mrc` family.

Save loader outputs as `01_file_inventory.csv` and `01_file_metadata.json`. If images are inspected visually, save representative raw/MIP/slice QC figures as `01_qc_*`.

If derived CSV/statistics files are supplied alongside raw microscopy data, do not use them as the measurement source at this stage. Register them as benchmark inputs in `01_file_inventory.csv` and defer comparison until after image-derived measurements are produced.

### Step 3 — Infer array layout

Run the dimension detector to classify the data as 2D / volumetric / multichannel / mixed, and record the routing hint. When layout is ambiguous (for example dim 0 could be Z or C), ask the user once before continuing.

Save layout decisions as `02_layout_detection.json` and any routing notes as `02_layout_notes.md`.

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

Save the retrieval request and evidence pack as `03_method_search_request.json` and `03_evidence_pack.json`. If network was skipped or unavailable, save `03_evidence_gap.md`.

### Step 5 — Recommend method and wait for approval

Before installing anything, modifying/adding analysis code, or running a full analysis for a new benchmark/task, present a short recommendation to the user:

- Best method and why it fits the data/task.
- Key evidence links from `ai4s-web-search`.
- Expected install/downloads, license, runtime/GPU risk, and output contract.
- Fallback option if the user declines the recommended method.
- Exact next actions that will happen only after approval.

Save this as `03_method_recommendation.md` and, when useful, `03_method_recommendation.json`.

Allowed before approval:

- Inspect input files and infer layout.
- Search the internet and build the evidence pack.
- Draft the recommendation and extension plan.

Not allowed before approval, unless the user already explicitly chose the method:

- `pip install`, `conda install`, `git clone`, model-weight downloads, Docker pulls, or other external setup.
- Adding new adapter/tool code for the method.
- Running the full benchmark/analysis or tuning parameters from benchmark labels.
- Treating a simpler baseline as final when evidence indicates a stronger task-specific method.

If the user approves the recommendation, continue to the approved built-in path or Step 7 controlled extension gate. If the user declines, ask whether to run the fallback baseline and clearly mark it as a lower-confidence fallback.

### Step 6 — Choose the approved analysis pathway

| Goal | Starting point |
|------|----------------|
| Detect and measure objects (2D) | Classical 2D segmentation (Otsu + watershed); optional DL segmenter if evidence supports it |
| Benchmark 2D fluorescence spot detection | First search current spot-detection methods. If evidence supports Spotiflow or another stronger method, recommend it and wait for approval before installing/writing adapters/running. If declined, use a clearly labeled classical LoG/DoG baseline. |
| Detect and measure objects (3D) | Interactive 3D thresholding pipeline (Gaussian → background subtraction → Otsu → 3D CC → regionprops) |
| Fluorescence intensity | Z-depth profile / attenuation correction |
| Colocalization | Pearson / Manders pixel-based; object-based if evidence supports it |
| Spatial statistics | Nearest-neighbor distance, density, size distribution |
| GFP / fluorescence preservation | Per-object intensity, SNR/CTCF, paired comparison if a control exists |

These are starting points. If the evidence pack recommends a stronger method, use the controlled extension gate instead of ad-hoc code.

Save the selected pathway and rejected alternatives as `04_pipeline_decision.md` and, when useful, `04_pipeline_decision.json`. Include the user approval text or state that approval was not required because the user explicitly selected a built-in method.

### Step 7 — Controlled extension / auto-install gate

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

Save extension artifacts as `05_extension_plan.md`, `05_extension_verification.json`, `05_extension_smoke_test.txt`, and `05_extension_provenance.json` when this gate is used. If no extension is needed, save `05_extension_status.json` with `{"status": "not_needed"}`.

### Step 8 — Run analysis and produce artifacts

Emit, at minimum:

- Intermediate tables and QC outputs produced during processing.
- Publication-quality figures (at least 200 dpi, scale bars, unit-labeled axes).
- Tabular outputs (CSV) with all measured quantities in physical units.
- A small JSON summary with method, parameters, counts, thresholds, evidence URLs, and extension provenance if any.

Units must be µm / µm² / µm³ / AU, never raw pixels only.

Default 3D object size reporting:

- Do not use GT, benchmark CSV, or derived statistics exports to fit any volume parameter. Benchmarks are for post hoc evaluation only.
- For Z-stacks with bottom-plane artifacts or substrate/contact regions, exclude the bottom low-Z portion before labeling when the user says low-Z should be removed. Default to a fixed 10% low-Z exclusion and log the crop range; do not tune the crop from CSV/GT.
- Apply the same kept Z range to benchmark CSV/statistics exports before post hoc comparison, and record benchmark object counts before/after filtering.
- Remove objects touching the low-Z crop boundary so truncated partial objects do not enter the statistics.
- Use `equivalent_diameter_um = (6 * volume_um3 / pi)^(1/3)` as the primary 3D object size metric when volume-derived error is too sensitive or when comparing against software exports that report volume.
- Always compute and save `voxel_filled_volume_um3 = foreground_voxels × voxel_volume`.
- When 3D labels are available and runtime is acceptable, default `volume_um3` to a non-GT surface/mesh estimate computed directly from the segmentation mask, e.g. marching cubes with calibrated voxel spacing.
- Always compute and save `equivalent_diameter_um` from the primary `volume_um3`; also save equivalent diameters for secondary volume modes when useful.
- Also save fixed secondary alternatives such as `boundary_alpha_0_5_volume_um3` for auditability, but do not fit alpha from benchmark data.
- If mesh volume fails or is too slow, fall back to `voxel_filled_volume_um3` as the primary physical mask volume and record the fallback.
- Always log `primary_size_metric`, `volume_mode`, `volume_source`, fallback status, `benchmark_used_for_volume_calibration: false`, and `benchmark_used_for_size_calibration: false` in the summary JSON.

Save final and intermediate processing outputs using stage prefixes, e.g. `06_intermediate_*`, `07_final_*`, `08_summary.json`. The final summary must include a manifest of every artifact path.

For corrected runs, also emit:

- `00_correction_feedback.md` — the user's reported error and the specific question/answer that clarified it.
- `08_correction_summary.json` — issue class, reflection, changed assumptions, changed parameters/code, before/after benchmark metrics, and remaining risks.
- Updated QC figures/tables for every recomputed stage.

### Step 9 — Follow-up context

After analysis, before ending the turn, collect experimental context using `prompts/followup.md`: sample, aim, channels, treatments, controls/comparators, and replicate status. Ask whether the user wants result interpretation handled by `lsm-result-interpret`.

Save this as `09_followup_context.md` or `09_followup_context.json`. If the user does not provide context, record missing fields explicitly.

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
| `prompts/artifact_contract.md` | Required intermediate and final output files |

---

## Anti-Patterns

- Do NOT run analysis before showing the user what the raw data looks like.
- Do NOT skip intermediate artifact outputs; final figures/tables alone are insufficient.
- Do NOT use derived CSV/statistics exports as the primary measurement source when raw microscopy images are available, unless the user explicitly requests table-only analysis.
- Do NOT skip layout detection when the array has more than two dimensions.
- Do NOT skip method search unless the user explicitly forbids network access.
- Do NOT auto-install packages, clone repos, download weights, or run external code without explicit user approval.
- Do NOT add large vendored trees or model weights to the skill repo.
- Do NOT write narrative reports or fabricate citations here; delegate interpretation to `lsm-result-interpret`.
- Do NOT report measurements in pixels only.
- Do NOT end an analysis turn without collecting follow-up context.
- Do NOT ignore user error reports or rerun the same pipeline unchanged after correction feedback.
- Do NOT overwrite earlier benchmark artifacts during correction unless the user explicitly requests replacement.
- Do NOT tune threshold, alpha, volume scale, or object filters from CSV/GT benchmark values unless the task is explicitly a supervised calibration experiment and the output is labeled as calibrated rather than default analysis.
- Do NOT claim fluorescence is preserved or destroyed without a control or literature/reference evidence.
