# Particle Tracking: Guiding Principles

## Prerequisites

- Data must have a time dimension (time-lapse)
- Need to know: frame interval (seconds), pixel size (µm)

## What to Ask

1. 2D tracking or 3D?
2. Approximate particle size?
3. How fast do particles move between frames? (for setting search range)
4. How many particles per frame?
5. Do particles appear/disappear, or are they always present?

## General Approach

1. **Detect** particles in each frame
2. **Link** detections across frames into trajectories
3. **Filter** short/spurious tracks
4. **Correct** for sample drift if needed
5. **Analyze**: MSD, diffusion coefficient, velocity, confinement

## When to Search

- Search for `trackpy` documentation for the standard Python tracking workflow
- If particles are dense/overlapping → search for deep-learning trackers (e.g., Trackastra)
- If tracking RNA spots (FISH) → search for Big-FISH
- If user needs sophisticated motion analysis → search for latest MSD analysis methods
- Always check the trackpy docs for correct API, as it may have been updated

## Key Caveats

- Tracking quality depends heavily on detection quality
- MSD analysis requires sufficiently long tracks (≥20 frames)
- Drift correction is essential for accurate diffusion measurements
- Anomalous diffusion (α ≠ 1) is common in biological systems — don't assume simple Brownian motion
