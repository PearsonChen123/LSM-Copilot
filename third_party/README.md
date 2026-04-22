# Third-party source (optional)

## Cellpose (2D / 3D cell segmentation)

Upstream: [MouseLand/cellpose](https://github.com/MouseLand/cellpose)  
License: **BSD-3-Clause** (see cloned `cellpose/LICENSE` after install)  
Documentation: https://cellpose.readthedocs.io/

### Option A — PyPI (recommended for CI and most users)

```bash
pip install cellpose
```

Follow the official installation guide for PyTorch / GPU:  
https://cellpose.readthedocs.io/en/latest/installation.html

### Option B — Vendor clone (follow upstream repo layout)

From the skill repository root:

```bash
bash scripts/clone_cellpose.sh
```

This performs a **shallow** `git clone` into `third_party/cellpose/`. The directory is **gitignored** in this repo to avoid committing large weights; run the script locally when you need to read upstream code or pin a revision.

**Attribution**: If you redistribute analyses derived from Cellpose, cite the Cellpose paper as requested in the upstream README.
