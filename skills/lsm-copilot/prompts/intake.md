# Intake: File Loading & Analysis Goal Determination

## Step 1: Identify Input File

Ask user for the microscopy image file path. Supported formats:

| Format | Extension | Reader | Auto-Metadata |
|--------|-----------|--------|---------------|
| Zeiss LSM | `.lsm` | `tifffile` | voxel size, channels, objective |
| Zeiss CZI | `.czi` | `aicspylibczi` or `czifile` | full OME metadata |
| Leica LIF | `.lif` | `readlif` | voxel size, series |
| OME-TIFF | `.ome.tif` | `tifffile` | OME-XML metadata |
| Plain TIFF | `.tif/.tiff` | `tifffile` | NONE — must ask user |

If plain TIFF without metadata, ask:
1. Voxel size in µm (Z, Y, X) — e.g., `0.44 0.17 0.17`
2. Number of channels
3. Dimension order (e.g., ZCYX, TZYX)

Run `file_reader.py` to load and display basic info:
```bash
python3 ${SKILL_DIR}/tools/file_reader.py <path> --info
```

## Step 2: Determine Analysis Goal

Present the 7 analysis routes (A-G) from SKILL.md.

If user is unsure, ask these diagnostic questions:
- "Do you want to **count or measure** objects?" → Route A (Segmentation)
- "Do you want to compare **two colors/channels**?" → Route C (Colocalization)
- "Do you want to see how **intensity changes with depth**?" → Route B (Intensity)
- "You already have detected objects and want to understand their **arrangement**?" → Route D (Spatial)
- "Is this a **time-lapse** movie?" → Route E (Tracking)
- "Is the image **noisy or blurry** and you want to clean it up?" → Route F (Enhancement)
- "Just want to **look around** first?" → Route G (Exploratory)

Multiple routes can be chained sequentially.

## Step 3: Sample Context (Optional)

Ask for context that affects algorithm choice:
- Material type (polymer, cell, tissue, nanoparticle)
- Expected object size range (nm, µm, mm)
- Bright objects on dark background, or dark objects on bright?
- Any known artifacts (photobleaching, scattering, autofluorescence)?
