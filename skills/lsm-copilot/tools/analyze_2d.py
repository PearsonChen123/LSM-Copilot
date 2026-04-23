#!/usr/bin/env python3
"""
2D fluorescence object detection (classical CV baseline).

Optional Cellpose: `pip install cellpose` — https://github.com/MouseLand/cellpose

Usage:
    python3 analyze_2d.py image.tif --channel 1 --output-dir ./out2d
    python3 analyze_2d.py stack.tif --mode mip --channel 1 --output-dir ./out2d
    python3 analyze_2d.py stack.tif --mode slice --z-index 11 --channel 1 --output-dir ./out2d
    python3 analyze_2d.py image.tif --cellpose --diameter 30 --channel 0 --output-dir ./out2d
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.filters import gaussian, threshold_otsu
from skimage.measure import regionprops
from skimage.segmentation import watershed

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))


def load_plane(path, voxel, mode, z_index, channel):
    from file_reader import load_image
    data, voxel_out, meta = load_image(path, voxel)

    if data.ndim == 2:
        plane = data.astype(np.float32)
        ch_tag = "YX"
    elif data.ndim == 3:
        a, y, x = data.shape
        if a <= 16:
            plane = data[int(channel)].astype(np.float32)
            ch_tag = "C%d" % int(channel)
        else:
            if mode == "mip":
                plane = data.max(axis=0).astype(np.float32)
                ch_tag = "MIP_ZYX"
            else:
                zi = int(z_index) if z_index is not None else a // 2
                zi = max(0, min(zi, a - 1))
                plane = data[zi].astype(np.float32)
                ch_tag = "Z%d" % zi
    elif data.ndim == 4:
        z, c, y, x = data.shape
        if mode == "mip":
            plane = data[:, int(channel)].max(axis=0).astype(np.float32)
            ch_tag = "MIP_C%d" % int(channel)
        else:
            zi = int(z_index) if z_index is not None else z // 2
            zi = max(0, min(zi, z - 1))
            plane = data[zi, int(channel)].astype(np.float32)
            ch_tag = "Z%d_C%d" % (zi, int(channel))
    else:
        sys.exit("Unsupported shape %s for analyze_2d.py" % (data.shape,))

    return plane, voxel_out, meta, ch_tag


def segment_classical(plane, min_area=20, max_area=50000):
    sm = gaussian(plane, sigma=1.0, preserve_range=True)
    try:
        t = threshold_otsu(sm)
    except Exception:
        t = float(np.percentile(sm, 90))
    binary = sm > t
    binary = ndi.binary_opening(binary, iterations=1)
    binary = ndi.binary_closing(binary, iterations=2)
    distance = ndi.distance_transform_edt(binary)
    coords = peak_local_max(distance, min_distance=3, labels=binary.astype(np.int32))
    mask = np.zeros(distance.shape, dtype=np.int32)
    if coords.size:
        mask[tuple(coords.T)] = 1
    markers, _ = ndi.label(mask)
    if markers.max() == 0:
        labels, _ = ndi.label(binary)
    else:
        labels = watershed(-distance, markers, mask=binary)
    props = regionprops(labels, intensity_image=plane)
    rows = []
    uid = 0
    for p in props:
        if p.area < min_area or p.area > max_area:
            continue
        uid += 1
        im = p.image_intensity if hasattr(p, "image_intensity") else p.intensity_image
        mean_i = float(p.intensity_mean if hasattr(p, "intensity_mean") else p.mean_intensity)
        rows.append({
            "id": uid,
            "y": float(p.centroid[0]),
            "x": float(p.centroid[1]),
            "area_px": int(p.area),
            "mean_intensity": mean_i,
            "max_intensity": float(im.max()),
        })
    return labels, rows, float(t)


def segment_cellpose(plane, diameter, model_type="cyto2"):
    try:
        from cellpose import models
    except ImportError:
        sys.exit(
            "Cellpose not installed. See https://cellpose.readthedocs.io/en/latest/installation.html"
        )
    model = models.Cellpose(gpu=False, model_type=model_type)
    masks, flows, styles, diams = model.eval(plane, diameter=diameter, channels=[0, 0])
    props = regionprops(masks.astype(np.int32), intensity_image=plane)
    rows = []
    for i, p in enumerate(props, start=1):
        im = p.image_intensity if hasattr(p, "image_intensity") else p.intensity_image
        mean_i = float(p.intensity_mean if hasattr(p, "intensity_mean") else p.mean_intensity)
        rows.append({
            "id": i,
            "y": float(p.centroid[0]),
            "x": float(p.centroid[1]),
            "area_px": int(p.area),
            "mean_intensity": mean_i,
            "max_intensity": float(im.max()),
        })
    return masks.astype(np.int32), rows, float(diams)


def main():
    parser = argparse.ArgumentParser(description="2D segmentation + stats")
    parser.add_argument("input")
    parser.add_argument("--voxel", nargs=3, type=float, default=None, metavar=("VZ", "VY", "VX"))
    parser.add_argument("--mode", choices=["auto", "slice", "mip"], default="auto")
    parser.add_argument("--z-index", type=int, default=None)
    parser.add_argument("--channel", type=int, default=0)
    parser.add_argument("--min-area", type=int, default=20)
    parser.add_argument("--max-area", type=int, default=50000)
    parser.add_argument("--cellpose", action="store_true")
    parser.add_argument("--diameter", type=float, default=30.0)
    parser.add_argument("--cellpose-model", type=str, default="cyto2")
    parser.add_argument("--output-dir", type=str, default=".")
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    mode = args.mode
    if mode == "auto":
        from file_reader import load_image
        d, _, _ = load_image(args.input, args.voxel)
        mode = "mip" if d.ndim == 4 else "slice"

    plane, voxel_out, meta, ch_tag = load_plane(
        args.input, args.voxel, mode, args.z_index, args.channel
    )
    vy_um, vx_um = float(voxel_out[1]), float(voxel_out[2])

    if args.cellpose:
        labels, rows, thr_or_d = segment_cellpose(plane, args.diameter, args.cellpose_model)
        method = "cellpose_" + args.cellpose_model
    else:
        labels, rows, thr_or_d = segment_classical(plane, args.min_area, args.max_area)
        method = "classical_otsu_watershed"

    csv_path = out / "objects_2d.csv"
    with open(csv_path, "w") as f:
        f.write("id,y_px,x_px,y_um,x_um,area_px,area_um2,mean_intensity,max_intensity\n")
        for r in rows:
            y_um = r["y"] * vy_um
            x_um = r["x"] * vx_um
            area_um2 = r["area_px"] * vy_um * vx_um
            f.write("%d,%.2f,%.2f,%.3f,%.3f,%d,%.3f,%.2f,%.2f\n" % (
                r["id"], r["y"], r["x"], y_um, x_um, r["area_px"], area_um2,
                r["mean_intensity"], r["max_intensity"]))

    summary = {
        "input": str(Path(args.input).resolve()),
        "plane_tag": ch_tag,
        "method": method,
        "threshold_or_diameter": thr_or_d,
        "n_objects": len(rows),
        "voxel_um_yx": [vy_um, vx_um],
    }
    with open(out / "summary_2d.json", "w") as f:
        json.dump(summary, f, indent=2)

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    axes[0].imshow(plane, cmap="gray")
    axes[0].set_title("Input " + ch_tag)
    axes[1].imshow(labels, cmap="nipy_spectral")
    axes[1].set_title("Labels n=%d" % len(rows))
    g = plane / (plane.max() + 1e-8)
    rgb = plt.cm.gray(g)[:, :, :3]
    ov = rgb.copy()
    if labels.max() > 0:
        ov[labels > 0, 0] = 1.0
        ov[labels > 0, 1] = 0.2
        ov[labels > 0, 2] = 0.2
    axes[2].imshow(np.clip(ov, 0, 1))
    axes[2].set_title("Overlay")
    for ax in axes:
        ax.axis("off")
    fig.suptitle("2D analysis — " + method, fontsize=11, fontweight="bold")
    plt.tight_layout()
    fig.savefig(out / "Fig2d_segmentation.png", dpi=200, bbox_inches="tight")
    plt.close()

    print(json.dumps(summary, indent=2))
    print("Saved:", csv_path, "Fig2d_segmentation.png summary_2d.json")


if __name__ == "__main__":
    main()
