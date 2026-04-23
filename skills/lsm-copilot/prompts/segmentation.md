# Segmentation: Guiding Principles

## What to Ask the User First

1. Objects are bright on dark, or dark on bright?
2. Approximate object size (µm)?
3. Are objects touching/overlapping, or well-separated?
4. 2D slices or full 3D volumetric?
5. How many objects roughly? (tens, hundreds, thousands?)

## Classical Approach (built-in)

`gui_threshold.py` works well for well-separated objects with clear contrast. Start here.

If it works → done. If not → consider deep learning.

## When to Search for Alternatives

- Objects touching → search for watershed, Cellpose, or StarDist
- Very noisy → search for denoising first, then segment
- Non-round shapes → search for Cellpose (handles irregular shapes)
- User mentions a specific tool → search for its documentation
- Classical fails after parameter tuning → time to try DL

## Key Considerations

- Always account for **voxel anisotropy** in 3D (Z is typically 2-5x coarser than XY)
- Small objects near the Z-range edges are unreliable (laser attenuation, PSF degradation)
- **Ask the user to validate** a few detected objects visually before trusting bulk statistics
- Export both raw measurements (pixels) and calibrated measurements (µm, µm³)
