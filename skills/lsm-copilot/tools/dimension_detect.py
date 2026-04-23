#!/usr/bin/env python3
"""
Infer microscopy array layout (2D vs 3D vs multichannel) from loaded voxel data.

Usage:
    python3 dimension_detect.py /path/to/image.tif
    python3 dimension_detect.py /path/to/image.lsm --json

Does not modify files; prints a routing hint for agents and humans.
"""
import argparse
import json
import sys
from pathlib import Path

# Allow running from the skill root or tools/
_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))


def _guess_layout(shape):
    """Return (layout_tag, notes) for numpy shape after squeeze."""
    if len(shape) == 2:
        return "YX", ["Single 2D plane (grayscale or one channel)."]

    if len(shape) == 3:
        a, b, c = shape
        # Heuristic: if first dim is small (channels) and last two match large XY
        if a <= 16 and b >= 64 and c >= 64 and abs(b - c) < max(b, c) * 0.2:
            return "CYX", [f"First dim small ({a}); treating as channels (C×Y×X). Verify with metadata."]
        if a >= 8 and b >= 64 and c >= 64:
            return "ZYX", [f"First dim ({a}) plausibly Z; treating as Z×Y×X stack."]
        return "ZYX_or_CYX", ["Ambiguous 3D tensor; confirm Z vs C from OME / acquisition software."]

    if len(shape) == 4:
        z, c, y, x = shape
        return "ZCYX", [f"4D volume Z={z}, C={c}, Y={y}, X={x} (typical OME-TIFF / confocal export)."]

    if len(shape) == 5:
        return "5D", ["Likely TZCYX or similar; inspect metadata for dimension order."]

    return "UNKNOWN", [f"Unusual rank {len(shape)}; shape={shape}"]


def classify(shape):
    layout, notes = _guess_layout(shape)
    ndim = len(shape)

    if layout == "YX":
        route = "2D_classical_or_cellpose"
    elif layout == "CYX":
        route = "2D_per_channel_then_merge"
    elif layout == "ZYX":
        route = "3D_stack_or_project_to_2D"
    elif layout == "ZCYX":
        route = "3D_multichannel_or_slice_wise_2D"
    elif layout == "ZYX_or_CYX":
        route = "ASK_USER_THEN_BRANCH"
    else:
        route = "MANUAL_REVIEW"

    return {
        "shape": list(shape),
        "ndim": ndim,
        "layout_guess": layout,
        "routing_hint": route,
        "notes": notes,
    }


def main():
    parser = argparse.ArgumentParser(description="Detect 2D vs 3D layout from microscopy file")
    parser.add_argument("input", help="Image path")
    parser.add_argument("--voxel", nargs=3, type=float, default=None, metavar=("VZ", "VY", "VX"))
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    from file_reader import load_image

    data, voxel, meta = load_image(args.input, args.voxel)
    shape = data.shape
    info = classify(shape)
    info["voxel_um"] = list(voxel)
    info["format_meta"] = {k: meta[k] for k in ("format",) if k in meta}
    if meta.get("format") == "MRC":
        info["format_meta"]["mrc_mode"] = meta.get("mrc_mode")

    if args.json:
        print(json.dumps(info, indent=2))
        return

    print("=" * 60)
    print("  Dimension routing")
    print("=" * 60)
    print(f"  File       : {Path(args.input).name}")
    print(f"  Shape      : {shape}")
    print(f"  Layout     : {info['layout_guess']}")
    print(f"  Route      : {info['routing_hint']}")
    print(f"  Voxel (µm) : {voxel[0]:.4f} × {voxel[1]:.4f} × {voxel[2]:.4f}")
    for n in info["notes"]:
        print(f"  Note       : {n}")
    print("=" * 60)
    print("\nNext steps:")
    if info["routing_hint"].startswith("2D"):
        print("  → Run: python3 ${SKILL_DIR}/tools/analyze_2d.py <path> [--channel 0]")
    elif "3D" in info["routing_hint"] or "slice" in info["routing_hint"]:
        print("  → 3D: ${SKILL_DIR}/tools/gui_threshold.py / custom 3D pipeline")
        print("  → Optional 2D slice / MIP: ${SKILL_DIR}/tools/analyze_2d.py --mode slice --z-index N")
        print("           or ${SKILL_DIR}/tools/analyze_2d.py --mode mip --channel C")
    else:
        print("  → Ask user for Z vs channel order, then re-run.")


if __name__ == "__main__":
    main()
