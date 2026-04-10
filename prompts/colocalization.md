# Colocalization: Guiding Principles

## Before Computing Anything

1. Confirm the image has ≥2 channels
2. Ask what each channel represents (e.g., "green = protein A, red = protein B")
3. Check for **bleed-through** between channels — if present, metrics are meaningless
4. Ask: "Do you want to know if A and B are in the same place (co-occurrence), or if their intensities correlate (correlation)?"

## Key Metrics (know what they mean)

- **Pearson's r**: Do the two channels' intensities go up and down together? Sensitive to background.
- **Manders' M1/M2**: What fraction of channel 1 is found where channel 2 is? NOT symmetric.
- **Li's ICQ**: Quick yes/no — do the channels co-vary?

## Common Pitfalls

- High Pearson can be an artifact of shared background
- Always subtract background before computing metrics
- Manders requires a threshold — the choice of threshold matters a lot
- Colocalization ≠ molecular interaction (only means they're in the same ~200nm voxel)
- Always run significance test (e.g., Costes randomization)

## When to Search

- User needs object-based colocalization (not pixel-based) → search for latest methods
- User mentions specific metrics (Costes, Van Steensel) → look up correct implementation
- 3D colocalization on Z-stacks → search for ColocZStats or similar
- Cross-talk / spectral unmixing needed → search for linear unmixing methods
