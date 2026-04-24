# Quantification Metrics Quick Reference

## Morphology

| Metric | What It Tells You |
|--------|-------------------|
| Volume | 3D size. Must use calibrated voxel size and must record the calculation mode. |
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

## 3D Size and Volume Modes

For segmented confocal/LSM objects, prefer `equivalent_diameter_um` as the primary size metric when volume-derived error is too sensitive. Volume scales with diameter cubed, so small boundary differences can look large in volume space.

Save the mode and inputs:

- `equivalent_diameter_um`: `(6 * volume_um3 / pi)^(1/3)`, computed from the selected non-GT primary volume.
- `voxel_filled_volume_um3`: foreground voxel count multiplied by calibrated voxel volume.
- `surface_mesh_volume_um3`: mesh volume computed directly from the 3D binary object mask, e.g. marching cubes with calibrated Z/Y/X voxel spacing. Use this as the default surface-style volume when available.
- `boundary_alpha_0_5_volume_um3`: interior voxels plus half-weighted boundary voxels; useful as a conservative surface-style estimate.

CSV/GT benchmark exports must not be used to tune alpha, volume scale, threshold, or object filters in the default workflow. They are valid only for post hoc discrepancy reporting. If a user explicitly requests supervised calibration, label the output as calibrated and keep it separate from default analysis.

For Z-stacks with bottom-plane artifacts, substrate/contact regions, or user feedback that low-Z should be removed, apply a fixed low-Z crop before labeling and remove objects touching the crop boundary. Apply the same kept Z range to benchmark CSV/statistics rows before post hoc comparison. Record the excluded fraction/slices and benchmark counts before/after filtering; do not choose the crop from CSV/GT benchmark performance.

If mesh volume is unavailable or too slow, use `voxel_filled_volume_um3` as the primary physical mask volume and compute `equivalent_diameter_um` from that fallback. Always log `primary_size_metric`, `volume_mode`, `volume_source`, `benchmark_used_for_volume_calibration: false`, and `benchmark_used_for_size_calibration: false`.
