# Spatial Distribution: Guiding Principles

## What Researchers Usually Want to Know

- "Are my particles clustered or randomly distributed?"
- "Is there a gradient from top to bottom of the sample?"
- "How uniform is the size distribution?"
- "What's the typical spacing between objects?"

## Built-in Tool

`spatial_stats.py` takes a `spheres.csv` (output from segmentation) and computes:
- Nearest neighbor distances
- Z-segment statistics (count and avg volume per segment)
- Size distribution (mean, median, CV, percentiles)

## When to Go Beyond the Built-in

- User wants clustering analysis → search for DBSCAN, HDBSCAN in scikit-learn
- User wants Ripley's K function → search for `astropy` or `pointpats` library
- User wants Voronoi analysis → search for `scipy.spatial.Voronoi`
- User wants to compare two samples statistically → search for appropriate statistical tests (KS test, Mann-Whitney)

## Interpretation Hints

- CV < 30%: very uniform → controlled nucleation
- CV > 60%: highly polydisperse → Ostwald ripening or multiple nucleation events
- NND much smaller than random → clustering / aggregation
- Object size increases with depth → sedimentation or depth-dependent growth
- These are starting points — always discuss with the researcher and check against literature for their specific system
