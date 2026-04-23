# Image Enhancement: Guiding Principles

## First, Diagnose the Problem

Ask the user: what's wrong with your image?
- Grainy/speckled → noise
- Blurry/out-of-focus → needs deconvolution or just re-image
- Dim/low contrast → may need contrast enhancement
- Uneven brightness across the field → illumination correction

## General Principles

- Enhancement should be the **first step**, before any quantitative analysis
- Always keep the original data — enhance on a copy
- Aggressive denoising can remove real signal — always compare before/after
- If the image is fundamentally bad (wrong exposure, wrong focus), no algorithm can fully rescue it

## When to Search

- **Always search** for the latest denoising/restoration methods. This field evolves very fast.
- Key terms to search: "microscopy image denoising 2025", "Cellpose3 image restoration", "CARE CSBDeep", "Noise2Void"
- If user has paired training data (low/high quality) → search for supervised methods (CARE)
- If user has NO training data → search for self-supervised methods (Noise2Void, Noise2Self)
- For deconvolution → search for PSF estimation and Richardson-Lucy, or blind deconvolution

## Do NOT Hardcode Methods

Enhancement is the most rapidly evolving area of microscopy image analysis. What was best practice 6 months ago may be outdated. Always verify with a web search.

If the chosen restoration method requires a new package, model, or repo clone, follow `prompts/extension.md` before installation or integration.
