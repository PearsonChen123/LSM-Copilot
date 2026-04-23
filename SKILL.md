---
name: lsm-copilot
description: "Microscopy data-analysis skill in the LSM-Copilot suite. Owns loading, layout inference, pipeline selection, and quantification. The agent main loop delegates web search to `ai4s-web-search` and result discussion to `lsm-result-interpret`."
version: "3.0.0"
---

# lsm-copilot (Analysis skill in the LSM-Copilot suite)

"LSM-Copilot" is a **suite of Cursor Agent skills**, not a single skill. The agent's main loop decides which skill to invoke and routes artifacts between them. This document describes only **one member** of the suite: the **microscopy data-analysis** skill.

Sibling skills in the suite:

- **`ai4s-web-search`** — grounded retrieval of methods, tools, and reference values.
- **`lsm-result-interpret`** — evidence-backed interpretation of analysis outputs.

Skills never call each other directly; the agent is responsible for composition.

---

## Philosophy

- The suite is a set of narrow, composable skills; this document describes **one** of them. Orchestration lives in the agent main loop (see `README.md`).
- Understand the **scientific question** before touching code.
- Do not assume the best method — let the agent invoke `ai4s-web-search` once requirements and data layout are known.
- Do not hardcode parameters; show intermediate results and iterate with the user.
- Microscopy analysis is sample-dependent; always attach physical units (µm, µm³, AU).

---

## Trigger Conditions

Activate when the user mentions: microscopy, fluorescence, confocal, Z-stack, LSM/CZI/LIF/TIFF/MRC, segmentation, colocalization, particle tracking, droplet / cell counting, intensity analysis, GFP signal preservation.

If the user explicitly asks for **interpretation / discussion only** (not analysis), hand off directly to `lsm-result-interpret`.

---

## Role in the Agent Main Loop

The agent's main loop runs roughly as follows. This skill is the **data-analysis member**; the agent, not this skill, performs routing.

```
observe user request
│
├── if analysis task:
│     invoke this skill
│        ├── Step 1  clarify goal
│        ├── Step 2  load + inspect
│        ├── Step 2b infer layout
│        ├── Step 2c request evidence  ───► ai4s-web-search
│        ├── Step 3  choose pipeline (evidence-grounded)
│        ├── Step 4  run analysis, emit artifacts
│        └── Step 5  collect experimental context (follow-up)
│
├── if the user then wants interpretation:
│     invoke  lsm-result-interpret
│        with  { artifacts, experimental_context, evidence_pack }
│
└── if the user only wants grounded retrieval:
      invoke  ai4s-web-search  directly
```

This skill must not attempt to perform web search or write interpretive discussion. If the agent needs those, it calls the sibling skill.

---

## Workflow

### Step 1 — Clarify the scientific question

Ask briefly: what is the sample, what to measure, what the data looks like, and the file format.

### Step 2 — Load & inspect data

Use the built-in loader to print dimensions, voxel size, intensity range, and a representative slice. Supported formats: `.lsm`, `.czi`, `.lif`, `.tif`, `.mrc` family.

### Step 2b — Infer array layout

Run the dimension detector to classify the data as 2D / volumetric / multichannel / mixed, and record the routing hint. When layout is ambiguous (e.g., dim 0 could be Z or C), ask the user once before continuing.

### Step 2c — Hand off to `ai4s-web-search` (mandatory unless user forbids network)

Once requirements are clear **and** the layout is known, build a retrieval request:

```yaml
purpose: method_discovery
goal: "<stated analysis goal>"
domain_descriptors: ["fluorescence microscopy", "<layout>", "<modality tags>"]
constraints: ["open source", "python"]
k: 3
```

Invoke `ai4s-web-search` and wait for its **evidence pack** (JSON + optional summary). Use the shortlisted methods to justify pipeline choice; if the pack is empty or `confidence: low`, fall back to built-in tools and log the gap.

If the user explicitly declines network use, skip this step and note it in the final artifacts.

### Step 3 — Choose the analysis pathway

| Goal | Starting point |
|------|----------------|
| Detect & measure objects (2D) | Classical 2D segmentation (Otsu + watershed); optional DL segmenter if evidence supports it |
| Detect & measure objects (3D) | Interactive 3D thresholding pipeline (Gaussian → background subtraction → Otsu → 3D CC → regionprops) |
| Fluorescence intensity | Z-depth profile / attenuation correction |
| Colocalization | Pearson / Manders pixel-based; object-based if evidence supports it |
| Spatial statistics | Nearest-neighbor distance, density, size distribution |
| GFP / fluorescence preservation | Per-object intensity, SNR/CTCF, paired comparison if a control exists |

The tools are **starting points**. If the evidence pack suggests something stronger, use it (respect license and install notes).

### Step 4 — Run analysis and produce artifacts

Emit, at minimum:

- Publication-quality figures (≥ 200 dpi, scale bars, unit-labeled axes).
- Tabular outputs (CSV) with all measured quantities in physical units.
- A small JSON summary (method, parameters, counts, thresholds).

Units must be µm / µm² / µm³ / AU — never raw pixels.

### Step 5 — Follow-up (mandatory)

After analysis, **before ending your turn**, collect experimental context (sample, aim, channels, treatments, comparators) using `prompts/followup.md`. Ask whether the user wants a **result interpretation** (handled by `lsm-result-interpret`), not a full paper draft.

### Step 6 — Hand off to `lsm-result-interpret` (on request)

If the user wants interpretation / discussion, assemble the handoff payload:

- `analysis_artifacts` — paths to summary, figures, parameters, units.
- `experimental_context` — from Step 5.
- `evidence_pack` — from Step 2c, plus an optional second round asking `ai4s-web-search` for **reference values** (purpose: `reference_values`).

Invoke `lsm-result-interpret` and return its output to the user.

If the user only wants raw numbers, stop at Step 5.

---

## Fluorescence Preservation (task module, not a separate phase)

Relevant when comparing fluorescence before vs after a preparation method, across conditions, or when validating that a treatment did not destroy signal. Metrics: per-object mean intensity, intensity distributions, SNR / SBR, integrated density / CTCF, coefficient of variation. Stats: Mann-Whitney / t-test (2 groups), Kruskal-Wallis / ANOVA (3+ groups). Single-sample case requires explicit caveat language; interpretation versus reference values is delegated to `lsm-result-interpret`.

See `prompts/fluorescence_preservation.md` for the full template.

---

## Built-in Capabilities (role descriptions)

This skill provides lightweight Python utilities under `tools/` for: universal file loading, layout detection, 2D classical segmentation, 3D interactive thresholding, intensity profiling, basic colocalization, spatial statistics, and batch processing. Exact filenames and CLI flags are documented in `README.md`; they are intentionally **not** enumerated here because this document is workflow-facing.

For anything outside these capabilities, prefer the method returned by `ai4s-web-search` (respecting license and install instructions) over ad-hoc code.

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
- Do NOT skip Step 2b (layout detection) when the array has more than two dimensions.
- Do NOT skip Step 2c unless the user explicitly forbids web access; analysis choices must be evidence-led.
- Do NOT write narrative reports or fabricate citations here — delegate to `lsm-result-interpret`.
- Do NOT report measurements in pixels; always attach physical units.
- Do NOT end your turn after analysis without running Step 5 (context follow-up).
- Do NOT claim fluorescence is "preserved" or "destroyed" without a control or literature reference.
