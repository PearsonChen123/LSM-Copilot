# LSM-Copilot

> **A suite of collaborating Cursor Agent skills for fluorescence / confocal microscopy image analysis.**

LSM-Copilot is **not a single skill**. It is a **skill suite** plus the agent's main loop. The agent observes the user's request, decides which skill to invoke, routes artifacts between skills, and returns a final answer. Each skill has a narrow, well-defined job and a clean handoff contract.

---

## Skill Suite

| Skill | Scope | Owns |
|-------|-------|------|
| `lsm-copilot` (this folder) | Microscopy **data analysis** | Data loading, layout inference, pipeline selection, computation, QC, artifacts |
| `ai4s-web-search` (generic) | **Grounded retrieval** | Building queries, executing web search, returning a structured evidence pack |
| `lsm-result-interpret` | **Result interpretation** | Turning artifacts + evidence into a structured discussion (no full reports) |

Sibling skills live at `.cursor/skills/ai4s-web-search/` and `.cursor/skills/lsm-result-interpret/`.

---

## Agent Main Loop (how the skills compose)

The agent runs a simple loop. At each step it picks the skill that best fits the current state; skills never call each other directly — the agent does the routing.

```
observe user request
│
├─► does it describe raw data / an analysis task?
│     └─► invoke  lsm-copilot
│           ├── clarify goal
│           ├── load + inspect data
│           ├── infer array layout (2D / volumetric / multichannel / mixed)
│           ├── request evidence: invoke ai4s-web-search (purpose=method_discovery)
│           ├── choose pipeline grounded in the evidence pack
│           ├── run analysis, emit figures + tables + JSON summary
│           └── collect experimental context (follow-up)
│
├─► does the user want interpretation / discussion of existing results?
│     ├── if reference values are needed: invoke ai4s-web-search (purpose=reference_values)
│     └── invoke lsm-result-interpret with {artifacts, context, evidence_pack}
│
└─► does the user want grounded retrieval only?
      └─► invoke ai4s-web-search directly
```

The orchestration logic lives in the **agent**, not in any one skill. Each skill's `SKILL.md` documents only its own scope, inputs, and outputs.

---

## Scope of This Skill (`lsm-copilot`)

This skill handles **Phase-1 analysis**:

- Universal file loading for `.lsm`, `.czi`, `.lif`, `.tif`, `.mrc` family.
- Layout inference (2D / volumetric stack / multichannel / mixed) with a routing hint.
- Pipeline selection backed by the evidence pack from `ai4s-web-search`.
- Quantification: 2D / 3D object detection, intensity profiling, colocalization, spatial statistics, batch processing, fluorescence-preservation task module.
- Publication-quality figures, CSV tables, and JSON summaries with physical units.

It does **not** perform web search and does **not** draft narrative reports.

---

## Supported File Formats

| Format | Extension | Auto metadata |
|--------|-----------|---------------|
| Zeiss LSM | `.lsm` | yes (voxel, channels) |
| Zeiss CZI | `.czi` | yes |
| Leica LIF | `.lif` | yes |
| OME-TIFF | `.ome.tif` | yes |
| Plain TIFF | `.tif` | voxel to be provided |
| MRC family | `.mrc`, `.mrcs`, `.map`, `.rec`, `.st` | yes (voxel from header, Å → µm) |

---

## Install

### As Cursor agent skills (recommended)

Place all three skills under a `skills/` directory that Cursor scans:

```bash
mkdir -p .cursor/skills
git clone <repo-url> .cursor/skills/lsm-copilot
git clone <repo-url-for-search>  .cursor/skills/ai4s-web-search
git clone <repo-url-for-interp>  .cursor/skills/lsm-result-interpret
```

(If the three skills ship together, copy each subfolder into `.cursor/skills/`.)

### Python dependencies

```bash
pip install -r requirements.txt
```

Optional deep-learning segmenters (only if the evidence pack recommends them):

```bash
pip install cellpose
pip install stardist
```

---

## Handoff Contracts (quick reference)

### `lsm-copilot` → `ai4s-web-search`

```yaml
purpose:            method_discovery | reference_values | tool_verification | citation_grounding
goal:               "<one-sentence analysis goal>"
domain_descriptors: ["fluorescence microscopy", "<layout tag>", "<modality tags>"]
constraints:        ["open source", "python", "<others>"]
k:                  3
```

Returns: a JSON evidence pack (see `ai4s-web-search/templates/evidence_pack.md`).

### `lsm-copilot` → `lsm-result-interpret`

```yaml
analysis_artifacts:    { summary, figures, parameters, units }
experimental_context:  { sample, channels, treatments, aim, comparators }
evidence_pack:         <JSON from ai4s-web-search>
```

Returns: a structured interpretation block (see `lsm-result-interpret/templates/interpretation.md`).

---

## Project Structure

```
lsm-copilot/
├── SKILL.md                          # Agent-facing scope and workflow for this skill
├── README.md                         # This file
├── requirements.txt                  # Python dependencies
├── LICENSE
├── scripts/                          # Optional vendor-clone helpers
├── third_party/                      # Not committed by default
├── prompts/                          # Task-facing workflow templates
│   ├── intake.md
│   ├── dimension_routing.md
│   ├── segmentation.md
│   ├── intensity.md
│   ├── colocalization.md
│   ├── spatial.md
│   ├── tracking.md
│   ├── enhancement.md
│   ├── followup.md
│   └── fluorescence_preservation.md
├── tools/                            # Deterministic Python utilities
│   ├── file_reader.py
│   ├── dimension_detect.py
│   ├── analyze_2d.py
│   ├── gui_threshold.py
│   ├── intensity_profiler.py
│   ├── coloc_analyzer.py
│   ├── spatial_stats.py
│   └── batch_processor.py
├── knowledge/                        # Domain reference material
│   ├── algorithms.md
│   ├── file_formats.md
│   ├── metrics.md
│   └── deep_learning.md
├── archive/                          # Deprecated prompts (for provenance)
└── output/                           # Generated artifacts (gitignored)
```

---

## Design Philosophy

- **Narrow skills, orchestrating agent.** Each skill owns one responsibility; the agent composes them. This makes the system legible, testable, and easy to extend.
- **Evidence before execution.** The agent should retrieve methodological evidence (`ai4s-web-search`) after the user's goal and data layout are known, and before locking a pipeline.
- **Computation and interpretation are separate.** `lsm-copilot` produces numbers and figures; `lsm-result-interpret` turns them into evidence-backed discussion. No skill fabricates citations.
- **Human-in-the-loop.** Ambiguous layouts, missing controls, or thin evidence trigger explicit questions to the user rather than silent assumptions.
- **Physical units always.** Reports never appear in raw pixels.

---

## Contributing

To add a new analysis module to this skill:

1. Add a workflow template under `prompts/`.
2. Add a Python utility under `tools/`.
3. Extend the pipeline selection guidance in `SKILL.md`.
4. Update `knowledge/` if new domain references are needed.
5. If the module depends on third-party tools, document license and install in `third_party/README.md`.

To add a **new sibling skill** to the suite, create a new folder under `.cursor/skills/` with its own `SKILL.md` and a clear input/output contract, and reference it from the agent main-loop diagram above.

---

MIT License.
