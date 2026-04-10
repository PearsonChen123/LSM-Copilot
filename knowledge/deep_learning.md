# Deep Learning Tools for Microscopy

**WARNING**: This field evolves extremely fast. Always search the web for the latest version, API, and best practices before using any of these tools.

## Tools Worth Knowing About

| Tool | What It Does | Search For |
|------|-------------|------------|
| Cellpose | Cell/object segmentation (2D/3D) | "Cellpose3 documentation" |
| StarDist | Star-convex object detection | "StarDist 3D python" |
| napari | Interactive multi-dimensional viewer | "napari plugins [your task]" |
| CARE / CSBDeep | Image restoration (needs training pairs) | "CARE microscopy denoising" |
| Noise2Void | Self-supervised denoising (no pairs) | "Noise2Void python tutorial" |
| Spotiflow | Spot/puncta detection | "Spotiflow documentation" |
| Trackastra | DL-based particle tracking | "Trackastra tracking" |
| PhasorPy | FLIM phasor analysis | "PhasorPy documentation" |
| MicroLive | Live-cell analysis GUI | "MicroLive microscopy" |
| T-MIDAS | napari batch processing plugin | "T-MIDAS napari" |

## General Advice

- Don't use DL when classical methods work fine — it's slower to set up and harder to interpret
- Always check if pretrained models exist before training from scratch
- GPU dramatically speeds up inference; check availability with `torch.cuda.is_available()`
- Model APIs change between versions — **always read the current documentation**
