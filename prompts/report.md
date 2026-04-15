# Report Generation: Guiding Principles

## When to Generate

Only when the user explicitly requests a report (asked in Phase 2 follow-up). Never auto-generate.

---

## Before Writing: Search the Web (MANDATORY)

**You MUST search the web before writing any report.** This is not optional.

### What to Search For

Based on the sample context provided by the user, search for:

1. **The technique/method**: If user mentions a specific method (CryoChem, CLARITY, ExM, etc.), search for the original paper and key findings
2. **Reference values**: Search for typical measurements for the sample type
   - `"[cell type] nucleus diameter µm"` → to contextualize your size measurements
   - `"[tissue type] cell density per mm³"` → to compare your density numbers
   - `"[fluorescent protein] brightness preservation [fixation method]"` → for intensity context
3. **Methodological validation**: Search for papers that use similar analysis approaches
   - `"Otsu threshold nuclear segmentation confocal"` → to justify your method
   - `"3D connected component analysis microscopy"` → to cite the approach
4. **Domain-specific context**: What's the biological/material significance of your findings?

### How to Use Search Results

- **Cite specific numbers** from papers: "Mouse cortical neuron nuclei have been reported at 5–8 µm diameter (Author et al., Year), consistent with our measurement of 4.79 µm."
- **Acknowledge discrepancies**: If your numbers differ from literature, explain possible reasons.
- **Don't fabricate citations**: If you can't find a reference, say "to our knowledge" or "no direct comparison available in the literature."

---

## Report Structure

```markdown
# [Title: Descriptive, includes sample and method]

## 1. Background
- User-provided experimental context
- Brief literature context (from web search)
- Purpose of this analysis

## 2. Acquisition Parameters
- Table: file format, dimensions, voxel, physical size, channels, labels

## 3. Methods
- Image processing pipeline (step by step, with parameter values)
- Quantification metrics (what was measured and how)
- Statistical methods (if applicable)

## 4. Results
- 4.1 Detection/Segmentation (count, overview)
- 4.2 Morphometry (size, volume, shape — with literature comparison)
- 4.3 Fluorescence Intensity (profile, per-object, SNR)
- 4.4 Spatial Distribution (NND, density, patterns)
- 4.5 Fluorescence Preservation (if applicable)
- Each subsection references a figure

## 5. Discussion
- Key findings in context of user's scientific question
- Comparison to published values (from web search)
- Biological/material significance

## 6. Caveats and Limitations
- Be honest about what could be wrong
- Mention assumptions

## 7. Output Files
- Table listing all generated files

## 8. Conclusions
- 2-3 sentence summary of key takeaways
```

---

## Figure Standards

- 200+ dpi
- Proper axis labels with units (µm, µm³, not pixels)
- Scale bars on all microscopy images (white, with label)
- Colorbar if using pseudocolor
- Font size ≥ 8pt when printed at column width
- Panel labels: a), b), c)...
- Consistent color scheme across figures
- Figure titles as `Figure N. Descriptive title`

---

## Do NOT

- Generate boilerplate text that says nothing
- Over-interpret the data — if you're not sure what it means, say so
- Forget to mention limitations
- Assume you know the scientific context better than the researcher
- Skip the web search step — literature context is what makes the report valuable
- Fabricate references or statistics
