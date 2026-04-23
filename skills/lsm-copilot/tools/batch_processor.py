"""
Batch processor for running analysis pipelines on multiple microscopy files.

Usage:
    python batch_processor.py --input-dir /data/ --pattern "*.lsm" --pipeline segmentation
    python batch_processor.py --input-dir /data/ --pattern "*.tif" --pipeline intensity --voxel 0.44 0.17 0.17
"""
import argparse
import glob
import os
import sys
from pathlib import Path
from datetime import datetime


def find_files(input_dir, pattern):
    files = sorted(glob.glob(os.path.join(input_dir, pattern)))
    return files


def run_segmentation(filepath, output_dir, voxel=None):
    tool_dir = Path(__file__).parent
    cmd = f"python3 {tool_dir}/gui_threshold.py \"{filepath}\""
    if voxel:
        cmd += f" --voxel {voxel[0]} {voxel[1]} {voxel[2]}"
    print(f"  [segmentation] {cmd}")
    os.system(cmd)


def run_intensity(filepath, output_dir, voxel=None):
    tool_dir = Path(__file__).parent
    cmd = f"python3 {tool_dir}/intensity_profiler.py \"{filepath}\" --mode z-profile --output-dir \"{output_dir}\""
    if voxel:
        cmd += f" --voxel {voxel[0]} {voxel[1]} {voxel[2]}"
    print(f"  [intensity] {cmd}")
    os.system(cmd)


def run_info(filepath, voxel=None):
    tool_dir = Path(__file__).parent
    cmd = f"python3 {tool_dir}/file_reader.py \"{filepath}\" --info"
    if voxel:
        cmd += f" --voxel {voxel[0]} {voxel[1]} {voxel[2]}"
    os.system(cmd)


PIPELINES = {
    'segmentation': run_segmentation,
    'intensity': run_intensity,
    'info': lambda f, o, v: run_info(f, v),
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', required=True, help='Directory with images')
    parser.add_argument('--pattern', default='*.lsm', help='File glob pattern')
    parser.add_argument('--pipeline', choices=list(PIPELINES.keys()), default='info')
    parser.add_argument('--voxel', nargs=3, type=float, default=None)
    parser.add_argument('--output-dir', default=None, help='Base output directory')
    args = parser.parse_args()

    files = find_files(args.input_dir, args.pattern)
    if not files:
        print(f"No files matching '{args.pattern}' in {args.input_dir}")
        sys.exit(1)

    print(f"Found {len(files)} files matching '{args.pattern}'")

    if args.output_dir is None:
        args.output_dir = os.path.join(args.input_dir,
                                       f"batch_{args.pipeline}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    for i, f in enumerate(files):
        name = Path(f).stem
        out = os.path.join(args.output_dir, name)
        Path(out).mkdir(parents=True, exist_ok=True)
        print(f"\n[{i+1}/{len(files)}] Processing: {Path(f).name}")
        PIPELINES[args.pipeline](f, out, args.voxel)

    print(f"\nBatch complete. Results in {args.output_dir}/")
