# LSM-Copilot Skill Suite Layout

This repository is the **LSM-Copilot skill suite**. The suite is composed of three skill members:

| Skill | Location in this repo | Purpose |
|-------|-----------------------|---------|
| `ai4s-web-search` | `skills/ai4s-web-search/` | Grounded web retrieval for methods, tools, install facts, licenses, APIs, literature, and reference values |
| `lsm-copilot` | `skills/lsm-copilot/` | Microscopy data processing, controlled extension/install, quantification, QC, artifacts |
| `lsm-result-interpret` | `skills/lsm-result-interpret/` | Post-analysis interpretation backed by literature/reference evidence |

The agent main loop composes them; no skill calls another directly. See the top-level `README.md` and `skills/lsm-copilot/SKILL.md` for the flow diagram, controlled extension gate, and handoff contracts.

## Installing into Cursor

Copy or symlink each skill into Cursor's skills directory:

```bash
mkdir -p .cursor/skills
ln -s <repo>/skills/lsm-copilot      .cursor/skills/lsm-copilot
ln -s <repo>/skills/ai4s-web-search  .cursor/skills/ai4s-web-search
ln -s <repo>/skills/lsm-result-interpret .cursor/skills/lsm-result-interpret
```

`lsm-copilot` is the suite name and the data-processing member. Keep it as a sibling skill under `skills/lsm-copilot/`; do not symlink the repo root into `.cursor/skills`, because that creates recursive nesting.
