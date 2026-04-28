# Algorithm Selection Guide

This is a reference for choosing approaches. **Always verify with `ai4s-web-search` for the latest tools before committing to a pipeline.**

## Segmentation: Classical vs Deep Learning

| Situation | Try First | If It Fails |
|-----------|----------|-------------|
| Well-separated round objects | Otsu + connected components (gui_threshold.py) | Cellpose |
| Touching/overlapping objects | Cellpose or watershed | Search for latest instance segmentation |
| Star-convex nuclei | StarDist | Cellpose |
| Very noisy data | Denoise first, then segment | Cellpose3 has built-in restoration |
| Large dataset (>1000 images) | Classical (faster) | Fine-tune Cellpose on subset |

## 2D Spot Detection Benchmarks

For point-annotation benchmarks, do not evaluate a segmentation mask as if it were a spot detector. Use point predictions and one-to-one matching against ground-truth coordinates within a declared pixel radius.

Before implementing or running a benchmark pipeline, search current methods via `ai4s-web-search` and present a per-data recommendation to the user. Do not install any package, write an ad-hoc adapter script, or run a full benchmark until the user approves the chosen method.

No specific spot-detection tool is hardcoded as the answer. The right method depends on density, SNR, modality (FISH / puncta / single-molecule / live-cell), available pretrained models, and dataset splits — verify per dataset.

| Situation | Try First | If It Fails |
|-----------|----------|-------------|
| Any new spot-detection task | Run `ai4s-web-search` for current best-fit method; recommend with evidence and request approval | If declined or evidence is thin, offer a clearly labeled classical LoG/DoG fallback |
| Dataset has train/val/test splits | Select detector parameters on train/val only | Do not tune on test GT |
| Dense, noisy, subpixel spots | Verify a current DL spot detector fits the data; if approved, write a thin ad-hoc adapter script under `tools/extensions/` | Record install/model provenance and smoke-test before full run |

Always report precision, recall, F1, TP/FP/FN, matching radius, and localization error in pixels unless physical calibration is provided.

## Key Libraries to Search For

- **Cellpose**: General-purpose cell segmentation. Evolving fast — always check latest version.
- **StarDist**: Star-convex object detection. Fast, good for nuclei.
- **napari**: Interactive viewer with growing plugin ecosystem.
- **trackpy**: Particle tracking. Check docs for 3D support.
- **scikit-image**: Classical image processing. Stable, well-documented.
- **PhasorPy**: FLIM phasor analysis. Newer library — check current status.

## Rule of Thumb

Start simple (classical). If results are poor after reasonable parameter tuning, escalate to deep learning. Don't jump to DL just because it exists — classical methods are faster, more interpretable, and don't need GPUs.

If the best method requires a dependency that is not already supported, use the controlled extension gate in `prompts/extension.md`: verify evidence/license/install/API first, ask for approval, add a thin adapter, and smoke-test before full analysis.
