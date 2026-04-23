# Fluorescence Preservation Analysis

## Purpose

Quantify whether a sample preparation method (fixation, embedding, clearing, etc.) preserves fluorescent signals. This is critical for methods like CryoChem, CLARITY, iDISCO, and any protocol involving fluorescent proteins (GFP, tdTomato, mCherry, YFP, etc.).

---

## Two Scenarios

### Scenario A: Paired Comparison (control vs treated)

When the user has data from both conditions:

1. **Load both datasets** using `file_reader.py`
2. **Segment objects** in both using identical parameters
3. **Extract per-object intensities** from both
4. **Compare**:
   - Mean intensity (bar plot + individual data points)
   - Intensity distribution (overlaid histograms or violin plots)
   - SNR / SBR comparison
   - CTCF comparison
5. **Statistical test**:
   - Mann-Whitney U test (non-parametric, recommended for fluorescence data)
   - Report: n₁, n₂, mean ± SD for each, median, U statistic, p-value
   - Effect size: Cohen's d or rank-biserial correlation
6. **Interpretation**:
   - p > 0.05 + small effect size → "No significant difference in fluorescence intensity, suggesting adequate preservation"
   - p < 0.05 + large effect size → "Significant reduction/increase in fluorescence intensity"
   - Always note: intensity comparisons require matched imaging settings

### Scenario B: Single Sample (no control)

When only the processed sample is available:

1. **Measure per-object intensities** as normal
2. **Calculate SNR and CTCF**
3. **Search the web** for published reference values:
   - `"[fluorescent protein] intensity [tissue type] confocal"` 
   - `"[preparation method] fluorescence preservation [fluorescent protein]"`
   - `"[fluorescent protein] brightness comparison fixation methods"`
4. **Report with caveats**:
   - "Without a paired unfixed control, absolute fluorescence preservation cannot be quantified."
   - "The observed mean SNR of X.X and clearly resolved [objects] suggest that [fluorescent protein] signal is detectable after [preparation method]."
   - Compare to literature if available: "Published studies report [X]% retention of GFP fluorescence after [similar method] (Author et al., Year)."

---

## Key Metrics

| Metric | What It Tells You | How to Compute |
|--------|-------------------|----------------|
| Mean intensity ratio | Treated / Control signal level | mean(I_treated) / mean(I_control) |
| SNR | Signal quality | (I_object - I_background) / SD_background |
| CTCF | Background-corrected total fluorescence | IntDen - (Area × mean_background) |
| % retention | Fraction of signal preserved | (mean_treated / mean_control) × 100% |
| Distribution overlap | How similar the intensity profiles are | KS test D-statistic, Bhattacharyya distance |

---

## Figure Template

For the comparison figure, generate a 2×3 or 2×2 layout:

```
a) Mean intensity comparison     b) Intensity distribution overlay
   (bar + swarm/jitter)             (histogram or violin)

c) SNR comparison                d) Summary statistics table
   (box plot)                       (n, mean±SD, median, p-value)
```

For single-sample case:
```
a) Per-object intensity dist.    b) SNR distribution
c) Intensity vs size scatter     d) Summary + literature comparison
```

---

## Important Notes

- Fluorescence intensity is **not absolute** — it depends on laser power, detector gain, pinhole, immersion medium, and many other factors
- Comparisons are only valid when imaging settings are **identical** between conditions
- GFP and other fluorescent proteins can be quenched by pH, fixatives, or resin embedding — search for the specific protein's known sensitivities
- DRAQ5 and other chemical dyes behave differently from genetically encoded fluorescent proteins — don't mix them in preservation comparisons
