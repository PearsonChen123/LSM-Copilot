# Quantification Metrics Quick Reference

## Morphology

| Metric | What It Tells You |
|--------|-------------------|
| Volume | 3D size. Must use calibrated voxel size. |
| Equivalent diameter | Diameter of sphere with same volume |
| Sphericity | How round (1.0 = perfect sphere) |
| Aspect ratio | Elongation (1.0 = isotropic) |
| Solidity | Convexity (1.0 = fully convex, <1 = concave/irregular) |

## Colocalization

| Metric | Range | Key Point |
|--------|-------|-----------|
| Pearson's r | [-1, +1] | Sensitive to background. Subtract BG first. |
| Manders' M1/M2 | [0, 1] | NOT symmetric. M1 ≠ M2. Requires threshold. |
| Li's ICQ | [-0.5, +0.5] | Quick binary answer. |

## Spatial

| Metric | Interpretation |
|--------|---------------|
| CV (size) | <30% = uniform, >60% = highly polydisperse |
| Clark-Evans R | <1 = clustered, =1 = random, >1 = dispersed |
| NND | Mean spacing between nearest objects |

## Intensity

| Metric | What It Tells You |
|--------|-------------------|
| CTCF | Background-corrected total fluorescence per object |
| SNR | Image quality indicator |
| Attenuation coefficient µ | How fast signal drops with Z-depth |

## Fluorescence Preservation

| Metric | What It Tells You | Formula |
|--------|-------------------|---------|
| Intensity ratio | Signal level relative to control | mean(I_treated) / mean(I_control) |
| % retention | Fraction of signal preserved | ratio × 100% |
| SNR (single sample) | Whether signal is usable | (I_object − I_bg) / σ_bg |
| Distribution overlap | Similarity of intensity profiles | KS test D-statistic |
| CTCF ratio | Total fluorescence comparison | CTCF_treated / CTCF_control |

**Key considerations**:
- Fluorescence intensity is NOT absolute — depends on imaging settings
- Comparisons require **identical** laser power, gain, pinhole, immersion medium
- GFP is sensitive to pH < 6 and some fixatives (formaldehyde partially quenches)
- tdTomato is more resistant to fixation than GFP
- DRAQ5 (chemical dye) and GFP (genetic) have different preservation behaviors — don't mix in comparisons
- Without a paired control, compare to published reference values and note the limitation

These definitions are stable, but **always double-check the exact formula** when implementing — different sources may define metrics slightly differently.
