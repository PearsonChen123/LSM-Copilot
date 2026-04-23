# Third-Party Sources and Extension Provenance

This directory is for optional local source clones used by the controlled extension gate. Large source trees, model weights, and generated artifacts should not be committed.

For every approved third-party tool, record:

| Field | Required content |
|-------|------------------|
| Tool | Package or repository name |
| Source | GitHub / docs / paper URL |
| License | SPDX-style license when known, or `unknown` |
| Version | Package version, git tag, or commit SHA |
| Install | Exact command or official install URL |
| Adapter | Path under `tools/extensions/` if integrated |
| Citation | Paper or upstream citation note when requested |
| Status | `planned`, `installed`, `used`, `failed`, or `retired` |

Do not install, clone, or download third-party assets until the selected candidate has passed `ai4s-web-search` verification and the user has approved the extension plan.

---

## Cellpose (2D / 3D Cell Segmentation)

- Tool: `cellpose`
- Source: https://github.com/MouseLand/cellpose
- License: BSD-3-Clause, verify in the installed package or cloned `cellpose/LICENSE`
- Documentation: https://cellpose.readthedocs.io/
- Install: `pip install cellpose`
- Adapter: built into `tools/analyze_2d.py` via the optional `--cellpose` flag
- Status: optional

### Option A — PyPI

```bash
pip install cellpose
```

Follow the official installation guide for PyTorch / GPU:

https://cellpose.readthedocs.io/en/latest/installation.html

### Option B — Local Source Clone

From the skill repository root:

```bash
bash scripts/clone_cellpose.sh
```

This performs a shallow `git clone` into `third_party/cellpose/`. The directory is gitignored to avoid committing large upstream trees or weights.

Attribution: If you redistribute analyses derived from Cellpose, cite the Cellpose paper as requested by upstream.
