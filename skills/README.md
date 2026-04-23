# Skill Suite Layout

This repository is the **LSM-Copilot skill suite**. Three skills live here:

| Skill | Location in this repo | Purpose |
|-------|-----------------------|---------|
| `lsm-copilot` | **repo root** (`SKILL.md`, `tools/`, `prompts/`, `knowledge/`, ...) | Microscopy data analysis |
| `ai4s-web-search` | `skills/ai4s-web-search/` | Grounded web retrieval (evidence pack) |
| `lsm-result-interpret` | `skills/lsm-result-interpret/` | Evidence-backed result interpretation |

The agent main loop composes them; no skill calls another directly. See the top-level `README.md` for the flow diagram and handoff contracts.

## Installing into Cursor

Copy or symlink each skill into Cursor's skills directory:

```bash
mkdir -p .cursor/skills
ln -s <repo>/                        .cursor/skills/lsm-copilot
ln -s <repo>/skills/ai4s-web-search  .cursor/skills/ai4s-web-search
ln -s <repo>/skills/lsm-result-interpret .cursor/skills/lsm-result-interpret
```
