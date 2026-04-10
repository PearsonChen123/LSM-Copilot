# LSM-Copilot

> **Fluorescence & Confocal Microscopy Image Analysis AI Agent**

License: MIT Python 3.9+ Cursor Agent Skill

Your microscopy data is too complex to analyze manually?  
Your Z-stack has hundreds of slices and you need 3D quantification?  
Your multi-channel images need colocalization but you don't know ImageJ macros?  

**Let AI be your microscopy analysis copilot.**

Give it a microscopy file + a natural language description of what you want to analyze, and get **publication-ready quantification, figures, and CSV data**.

---

## Features

| Module | Capability |
|--------|-----------|
| **3D Segmentation** | Interactive GUI with Otsu threshold + 3D connected components, or Cellpose3/StarDist deep learning |
| **Intensity Analysis** | Z-depth profiling, laser attenuation correction, ROI quantification, photobleaching correction |
| **Colocalization** | Pearson, Manders, Li's ICQ, scatter plots, merged overlays |
| **Spatial Statistics** | Nearest neighbor distance, clustering analysis, Z-segment statistics, size distribution |
| **Particle Tracking** | Trackpy-based 2D/3D tracking, MSD, diffusion coefficients |
| **Image Enhancement** | Denoising, deconvolution, Cellpose3 restoration, CLAHE |
| **Batch Processing** | Process entire directories with consistent pipelines |
| **Report Generation** | Auto-generate structured scientific reports with figures |

## Supported File Formats

| Format | Extension | Auto-Metadata |
|--------|-----------|---------------|
| Zeiss LSM | `.lsm` | Yes (voxel, channels) |
| Zeiss CZI | `.czi` | Yes |
| Leica LIF | `.lif` | Yes |
| OME-TIFF | `.ome.tif` | Yes |
| Plain TIFF | `.tif` | Manual voxel input |

---

## Install

### As Cursor Agent Skill (recommended)

```bash
# Project-level (shared with collaborators)
mkdir -p .cursor/skills
git clone https://github.com/YOUR_USERNAME/lsm-copilot .cursor/skills/lsm-copilot

# Or global (available in all projects)
git clone https://github.com/YOUR_USERNAME/lsm-copilot ~/.cursor/skills/lsm-copilot
```

### Dependencies

```bash
pip install -r requirements.txt
```

For deep learning segmentation (optional):
```bash
pip install cellpose        # Cellpose3
pip install stardist        # StarDist
pip install "napari[all]"   # napari viewer
pip install trackpy pims    # particle tracking
```

---

## Usage

In Cursor, simply describe what you want:

```
"Help me analyze this LSM file, I want to detect all crystalline domains and measure their sizes"
```

The AI agent will:
1. Ask you for the file path and analysis goal
2. Select the appropriate analysis pipeline
3. Run the analysis with optimal parameters
4. Generate CSV data + publication-quality figures
5. Provide scientific interpretation

### Direct Tool Usage (CLI)

```bash
# File info
python tools/file_reader.py image.lsm --info

# Interactive 3D segmentation GUI
python tools/gui_threshold.py image.lsm

# Z-depth intensity profile
python tools/intensity_profiler.py image.lsm --mode z-profile

# Colocalization (2-channel)
python tools/coloc_analyzer.py image.lsm --ch1 0 --ch2 1

# Spatial statistics (from segmentation CSV)
python tools/spatial_stats.py spheres.csv --output-dir results/

# Batch processing
python tools/batch_processor.py --input-dir /data/ --pattern "*.lsm" --pipeline info
```

---

## Project Structure

```
lsm-copilot/
├── SKILL.md              # Agent Skill entry point & router
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── LICENSE               # MIT License
├── prompts/              # Analysis workflow templates
│   ├── intake.md         #   File & goal determination
│   ├── segmentation.md   #   3D object segmentation
│   ├── intensity.md      #   Fluorescence intensity analysis
│   ├── colocalization.md #   Multi-channel colocalization
│   ├── spatial.md        #   Spatial distribution statistics
│   ├── tracking.md       #   Particle tracking (time-lapse)
│   ├── enhancement.md    #   Image enhancement & restoration
│   └── report.md         #   Scientific report generation
├── tools/                # Python analysis scripts
│   ├── gui_threshold.py  #   Interactive 3D segmentation GUI
│   ├── file_reader.py    #   Universal microscopy file reader
│   ├── intensity_profiler.py   # Z-depth intensity analysis
│   ├── coloc_analyzer.py       # Colocalization metrics
│   ├── spatial_stats.py        # Spatial statistics
│   └── batch_processor.py      # Batch processing
├── knowledge/            # Domain knowledge (RAG)
│   ├── algorithms.md     #   Algorithm selection guide
│   ├── file_formats.md   #   File format reference
│   ├── metrics.md        #   Quantification metrics
│   └── deep_learning.md  #   DL tools (Cellpose, StarDist, napari)
└── output/               # Generated results (gitignored)
```

---

## How It Works (for AI4S researchers)

LSM-Copilot implements an **Agent Skill** architecture:

1. **SKILL.md** acts as a router — it matches user intent to analysis pipelines
2. **prompts/** contain domain-specific workflow templates that guide the AI through each analysis type
3. **tools/** provide deterministic Python scripts that the AI agent calls as tools
4. **knowledge/** serves as a RAG (Retrieval-Augmented Generation) knowledge base for algorithm selection and result interpretation

This architecture separates **scientific domain knowledge** (prompts + knowledge) from **computational implementation** (tools), making it easy to extend to new analysis types.

---

## Contributing

PRs welcome! To add a new analysis module:

1. Create `prompts/your_analysis.md` with the workflow template
2. Create `tools/your_tool.py` with the Python implementation
3. Add a route in `SKILL.md`
4. Add domain knowledge in `knowledge/` if needed
5. Update `requirements.txt` if new dependencies are introduced

---

MIT License
