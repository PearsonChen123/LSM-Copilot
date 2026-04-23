"""
Universal microscopy file reader.

Usage:
    python file_reader.py image.lsm --info
    python file_reader.py image.tif --voxel 0.44 0.17 0.17 --info
    python file_reader.py image.czi --info
    python file_reader.py image.mrc --info
"""
import sys
import argparse
import numpy as np
from pathlib import Path

def load_image(path, voxel=None):
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix in ('.lsm', '.tif', '.tiff', '.ome.tif'):
        import tifffile
        with tifffile.TiffFile(str(p)) as f:
            if f.is_lsm and voxel is None:
                meta = f.lsm_metadata
                vz = meta['VoxelSizeZ'] * 1e6
                vy = meta['VoxelSizeY'] * 1e6
                vx = meta['VoxelSizeX'] * 1e6
            elif voxel:
                vz, vy, vx = voxel
            else:
                vz, vy, vx = 1.0, 1.0, 1.0
            data = f.series[0].asarray().squeeze().astype(np.float32)
        return data, (vz, vy, vx), _extract_tiff_meta(f) if f.is_lsm else {}

    elif suffix == '.czi':
        try:
            from aicspylibczi import CziFile
            czi = CziFile(str(p))
            data, shp = czi.read_image()
            data = data.squeeze().astype(np.float32)
            vz, vy, vx = voxel if voxel else (1.0, 1.0, 1.0)
            return data, (vz, vy, vx), {'format': 'CZI'}
        except ImportError:
            sys.exit("CZI support requires: pip install aicspylibczi")

    elif suffix == '.lif':
        try:
            from readlif.reader import LifFile
            lif = LifFile(str(p))
            img = list(lif.get_iter_image())[0]
            stack = np.array([np.array(z) for z in img.get_iter_z()], dtype=np.float32)
            vz, vy, vx = voxel if voxel else (1.0, 1.0, 1.0)
            return stack, (vz, vy, vx), {'format': 'LIF', 'name': img.name}
        except ImportError:
            sys.exit("LIF support requires: pip install readlif")

    elif suffix in ('.mrc', '.mrcs', '.map', '.rec', '.st'):
        return _load_mrc(p, voxel)

    else:
        sys.exit(f"Unsupported format: {suffix}")


def _load_mrc(p, voxel=None):
    try:
        import mrcfile
    except ImportError:
        sys.exit("MRC support requires: pip install mrcfile")

    with mrcfile.open(str(p), permissive=True) as mrc:
        data = mrc.data.squeeze().astype(np.float32)
        vs = mrc.voxel_size

        if voxel:
            vz, vy, vx = voxel
        elif vs.x > 0 and vs.y > 0 and vs.z > 0:
            vx = float(vs.x) / 1e4  # Å → µm
            vy = float(vs.y) / 1e4
            vz = float(vs.z) / 1e4
        else:
            vx, vy, vz = 1.0, 1.0, 1.0

        h = mrc.header
        labels = []
        for i in range(min(int(h.nlabl), 10)):
            raw = h.label[i]
            txt = raw.decode('ascii', errors='ignore').strip() if isinstance(raw, bytes) else str(raw).strip()
            if txt:
                labels.append(txt)

        meta = {
            'format': 'MRC',
            'mrc_mode': int(h.mode),
            'cell_a': (float(h.cella.x), float(h.cella.y), float(h.cella.z)),
            'voxel_angstrom': (float(vs.z), float(vs.y), float(vs.x)),
            'labels': labels,
        }

    return data, (vz, vy, vx), meta


def _extract_tiff_meta(f):
    if not f.is_lsm:
        return {}
    m = f.lsm_metadata
    return {
        'format': 'LSM',
        'voxel_um': (m['VoxelSizeZ']*1e6, m['VoxelSizeY']*1e6, m['VoxelSizeX']*1e6),
        'dimensions': {k: m.get(f'Dimension{k}', None) for k in 'ZCYX'},
    }


def print_info(data, voxel, meta):
    print("=" * 60)
    print(f"  Format      : {meta.get('format', 'TIFF')}")
    print(f"  Shape       : {data.shape}")
    print(f"  Dtype       : {data.dtype}")
    ndim = data.ndim
    if ndim == 3:
        nz, ny, nx = data.shape
        print(f"  Z × Y × X  : {nz} × {ny} × {nx}")
        print(f"  Voxel (µm)  : {voxel[0]:.4f} × {voxel[1]:.4f} × {voxel[2]:.4f}")
        print(f"  Physical    : {nz*voxel[0]:.1f} × {ny*voxel[1]:.1f} × {nx*voxel[2]:.1f} µm")
    elif ndim == 4:
        print(f"  4D shape    : {data.shape} (likely Z×C×Y×X or T×Z×Y×X)")
        print(f"  Voxel (µm)  : {voxel[0]:.4f} × {voxel[1]:.4f} × {voxel[2]:.4f}")
    if meta.get('format') == 'MRC':
        print(f"  MRC mode    : {meta.get('mrc_mode')} "
              f"(0=int8, 1=int16, 2=float32, 6=uint16)")
        va = meta.get('voxel_angstrom', (0, 0, 0))
        print(f"  Voxel (Å)   : {va[0]:.1f} × {va[1]:.1f} × {va[2]:.1f}")
        for label in meta.get('labels', []):
            print(f"  Label       : {label}")
    print(f"  Intensity   : min={data.min():.1f}, max={data.max():.1f}, "
          f"mean={data.mean():.1f}, std={data.std():.1f}")
    print(f"  Memory      : {data.nbytes / 1e6:.1f} MB")
    print("=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Universal microscopy file reader')
    parser.add_argument('input', help='Input microscopy file')
    parser.add_argument('--voxel', nargs=3, type=float, default=None,
                        metavar=('VZ', 'VY', 'VX'), help='Voxel size in µm')
    parser.add_argument('--info', action='store_true', help='Print file info and exit')
    args = parser.parse_args()

    data, voxel, meta = load_image(args.input, args.voxel)
    if args.info:
        print_info(data, voxel, meta)
    else:
        print_info(data, voxel, meta)
        print("\nData loaded. Use load_image() in Python to access the array.")
