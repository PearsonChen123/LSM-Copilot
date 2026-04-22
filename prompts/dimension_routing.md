# Dimension Routing: 2D vs 3D Microscopy Data

## When to Use

Whenever the user provides a microscopy file and the analysis could be **2D-only**, **3D**, or **mixed** (e.g., Z-stack with optional 2D slice / MIP QC).

---

## Agent Checklist

### 1. Ask the user (before assuming)

Ask briefly:

1. **这张图像/数据是什么？**（组织、细胞、材料、哪篇文章的图等）
2. **分析目标**：只要 2D、只要 3D、还是 **3D 为主 + 2D 质控/对照**？
3. **是否有标尺 / voxel**：若 TIFF 无元数据，需要用户提供 **Z、Y、X 体素（µm）**。

### 2. Run dimension detection

```bash
python3 ${SKILL_DIR}/tools/dimension_detect.py <path> --json
```

Interpret `layout_guess` and `routing_hint`:

| `routing_hint` | Action |
|----------------|--------|
| `2D_classical_or_cellpose` | Run `analyze_2d.py` (classical or `--cellpose`) |
| `2D_per_channel_then_merge` | Run `analyze_2d.py` per channel, then summarize |
| `3D_stack_or_project_to_2D` | Default 3D pipeline; optionally `analyze_2d.py --mode mip` or `--mode slice` |
| `3D_multichannel_or_slice_wise_2D` | 3D + optional 2D per-Z or MIP for QC |
| `ASK_USER_THEN_BRANCH` | Ask whether dim0 is **Z** or **C** |

### 3. Search the web for methods (default: before running the main pipeline)

When the user’s **分析目标** is clear enough and you have **`routing_hint` / `layout_guess`**, search **before** committing to scripts — not only before report writing.

Build queries from **goal + modality + layout**, e.g.:

- `"[goal e.g. nuclear segmentation] confocal Z-stack python"` + mention `ZCYX` vs `ZYX` if relevant
- `"object-based colocalization multichannel 3D fluorescence"`
- `"cellpose 2D confocal segmentation installation"` / `"scikit-image watershed nuclei segmentation"` when segmentation is the goal

If deep learning is appropriate, prefer **Cellpose** ([GitHub](https://github.com/MouseLand/cellpose), [docs](https://cellpose.readthedocs.io/)) — BSD-3-Clause, `pip install cellpose` — but **confirm with search** that it fits the data type (e.g. 2D vs 3D, nuclei vs cyto).

### 4. Open-source compliance

- **Prefer `pip install cellpose`** per upstream docs.
- Optional local clone: `bash scripts/clone_cellpose.sh` → read `third_party/cellpose/LICENSE`.
- Do not commit large vendored trees; `third_party/cellpose/` is gitignored by default.

### 5. Choose tools and run analysis

Use **§3** web-search conclusions + the **§2** routing table to pick `analyze_2d.py`, 3D tools, or other libraries, then execute.

### 6. Run 2D analysis (when applicable)

Classical (no PyTorch):

```bash
python3 ${SKILL_DIR}/tools/analyze_2d.py image.tif --output-dir ./out2d --channel 0
```

Z-stack MIP on channel 1:

```bash
python3 ${SKILL_DIR}/tools/analyze_2d.py stack.tif --mode mip --channel 1 --voxel 1 0.39 0.39 --output-dir ./out2d
```

Cellpose (after `pip install cellpose`):

```bash
python3 ${SKILL_DIR}/tools/analyze_2d.py image.tif --cellpose --diameter 30 --channel 0 --output-dir ./out2d
```

---

## Outputs

- `objects_2d.csv` — centroids, areas (px and µm² if voxel known), intensities  
- `Fig2d_segmentation.png` — raw / labels / overlay  
- `summary_2d.json` — method, counts, parameters

---

## Anti-Patterns

- Do NOT skip the **§3 method search** after requirements and `routing_hint` are known (unless user forbids network).
- Do NOT assume ZCYX vs CYX without metadata — use `dimension_detect.py` + user confirmation when ambiguous.
- Do NOT bundle Cellpose weights into the skill git repo.
- Do NOT claim Cellpose results without citing upstream when writing papers.
