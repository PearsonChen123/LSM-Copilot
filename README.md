# LSM-Copilot

> A three-skill Cursor Agent suite for fluorescence / confocal microscopy analysis.

**LSM-Copilot** is the suite name. The suite is composed of three narrow skills connected by an agent-controlled flow:

| Skill member | Location | Scope |
|--------------|----------|-------|
| `ai4s-web-search` | `skills/ai4s-web-search/` | Grounded retrieval of methods, libraries, install notes, licenses, APIs, papers, and reference values. |
| `lsm-copilot` | `skills/lsm-copilot/` | Data processing: loading, layout inference, pipeline selection, controlled extension/install, quantification, QC, artifacts. |
| `lsm-result-interpret` | `skills/lsm-result-interpret/` | Post-analysis interpretation using artifacts, experimental context, and literature/reference evidence. |

The repo root is only the suite container. Each skill now lives under `skills/` as a sibling directory, which avoids recursive `.cursor/skills/lsm-copilot/skills/...` nesting.

---

## Skill Flow

```
User request
│
├─► Search / tool discovery / install verification only
│     └─► ai4s-web-search
│
├─► Raw data analysis or new analysis capability
│     └─► lsm-copilot
│           ├── inspect data + infer layout
│           ├── request method evidence ───────► ai4s-web-search
│           ├── choose a built-in pipeline
│           ├── if needed: controlled extension/install gate
│           │        ├── extension/tool verification ─► ai4s-web-search
│           │        ├── user approval for install/clone/download
│           │        ├── adapter under tools/extensions/
│           │        └── smoke test + provenance log
│           └── emit figures, CSV, JSON summaries
│
└─► Result interpretation / discussion
      └─► lsm-result-interpret
            ├── request literature/reference evidence ─► ai4s-web-search
            └── produce grounded interpretation
```

No skill silently installs packages or runs unreviewed external code. "Auto-extension" means the agent can carry out the discovery → verification → approval → install → adapter → smoke-test sequence end-to-end after the user approves the risky steps.

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

### Cursor skills

Copy or symlink all three skill members into Cursor's skills directory:

```bash
mkdir -p .cursor/skills
ln -s <repo>/skills/lsm-copilot      .cursor/skills/lsm-copilot
ln -s <repo>/skills/ai4s-web-search  .cursor/skills/ai4s-web-search
ln -s <repo>/skills/lsm-result-interpret .cursor/skills/lsm-result-interpret
```

Do not symlink the repo root into `.cursor/skills/lsm-copilot`; that recreates the nested skill loop.

### Python dependencies

```bash
pip install -r skills/lsm-copilot/requirements.txt
```

Optional deep-learning segmenters are installed only when the evidence pack and user approval justify them:

```bash
pip install cellpose
pip install stardist
```

Other third-party tools should go through the controlled extension gate documented in `skills/lsm-copilot/SKILL.md` and `skills/lsm-copilot/prompts/extension.md`.

---

## Project Structure

```
lsm-copilot/
├── README.md                         # This file
├── skills/
│   ├── lsm-copilot/
│   │   ├── SKILL.md                  # Data-processing skill contract
│   │   ├── requirements.txt          # Baseline Python dependencies
│   │   ├── scripts/                  # Optional helper scripts
│   │   ├── third_party/              # Optional local source clones
│   │   ├── prompts/                  # Workflow templates
│   │   ├── tools/                    # Deterministic Python utilities
│   │   └── knowledge/                # Domain reference material
│   ├── ai4s-web-search/
│   └── lsm-result-interpret/
└── output/                           # Generated artifacts, gitignored
```

---

## Handoff Contracts

### `lsm-copilot` → `ai4s-web-search`

```yaml
purpose: method_discovery | extension_discovery | tool_verification | reference_values | citation_grounding
goal: "<one-sentence analysis or extension goal>"
domain_descriptors: ["fluorescence microscopy", "<layout tag>", "<modality tags>"]
constraints: ["open source", "python", "<license/runtime constraints>"]
k: 3
```

Returns: a JSON evidence pack. For extension work, each candidate should include source URL, license, install notes, API entry points, maintenance signal, and caveats when known.

### `lsm-copilot` → `lsm-result-interpret`

```yaml
analysis_artifacts: { summary, figures, parameters, units }
experimental_context: { sample, channels, treatments, aim, comparators }
evidence_pack: <method evidence plus reference-value/literature evidence>
```

`lsm-result-interpret` should request `ai4s-web-search` first if the handoff does not include enough literature/reference evidence.

---

## Controlled Extension Policy

Use the extension gate when built-in tools cannot meet the analysis goal or when search finds a materially better open-source algorithm.

The required sequence is:

1. Define the missing capability and success criteria.
2. Search for candidate algorithms and verify install/license/API facts.
3. Present one selected candidate and a concise extension plan.
4. Ask for approval before `pip install`, `conda install`, `git clone`, model downloads, GPU/CUDA changes, or dependency-file edits.
5. Add a thin adapter under `skills/lsm-copilot/tools/extensions/`.
6. Record provenance in `skills/lsm-copilot/third_party/README.md` or the analysis JSON summary.
7. Run a smoke test before the full analysis.
8. Fall back to a built-in pipeline if install or verification fails.

---

## Contributing

To add a new built-in analysis module:

1. Add or update a workflow template under `skills/lsm-copilot/prompts/`.
2. Add deterministic code under `skills/lsm-copilot/tools/`.
3. Extend the pipeline selection guidance in `skills/lsm-copilot/SKILL.md`.
4. Update `skills/lsm-copilot/knowledge/` if new domain references are needed.
5. If third-party code is involved, document license, source, version/commit, install command, and citation notes in `skills/lsm-copilot/third_party/README.md`.

To add a new sibling skill, create a folder under `skills/` with its own `SKILL.md`, narrow scope, and explicit input/output contract, then update this README and the suite flow.

---

MIT License.
