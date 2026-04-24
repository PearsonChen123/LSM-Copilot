"""
Spatial distribution statistics for detected objects.

Usage:
    python spatial_stats.py spheres.csv --output-dir ./spatial_output/
"""
import argparse
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path


def load_spheres(csv_path):
    rows = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            diameter = r.get('diameter_um') or r.get('equivalent_diameter_um')
            volume = r.get('volume_um3') or r.get('surface_mesh_volume_um3') or r.get('voxel_filled_volume_um3')
            rows.append({
                'id': int(r.get('id') or r.get('label')),
                'cz': float(r.get('cz_um') or r.get('centroid_z_um')),
                'cy': float(r.get('cy_um') or r.get('centroid_y_um')),
                'cx': float(r.get('cx_um') or r.get('centroid_x_um')),
                'diameter': float(diameter),
                'volume': float(volume),
            })
    return rows


def nearest_neighbor_distances(spheres):
    from scipy.spatial import cKDTree
    coords = np.array([[s['cz'], s['cy'], s['cx']] for s in spheres])
    tree = cKDTree(coords)
    dd, _ = tree.query(coords, k=2)
    nnd = dd[:, 1]
    return nnd


def clark_evans_index(nnd, n_objects, volume_um3):
    """Clark-Evans Index: R = mean(NND) / expected(NND). R<1=clustered, R>1=dispersed."""
    density = n_objects / volume_um3
    expected_nnd = 0.5 / (density ** (1.0 / 3.0))
    observed_nnd = nnd.mean()
    return observed_nnd / expected_nnd if expected_nnd > 0 else np.nan


def z_segment_stats(spheres, n_segments=10):
    zs = np.array([s['cz'] for s in spheres])
    ds = np.array([s['diameter'] for s in spheres])
    vs = np.array([s['volume'] for s in spheres])
    z_min, z_max = zs.min(), zs.max()
    edges = np.linspace(z_min, z_max, n_segments + 1)
    segments = []
    for i in range(n_segments):
        mask = (zs >= edges[i]) & (zs < edges[i + 1])
        if i == n_segments - 1:
            mask = (zs >= edges[i]) & (zs <= edges[i + 1])
        count = mask.sum()
        avg_diam = ds[mask].mean() if count > 0 else 0
        avg_vol = vs[mask].mean() if count > 0 else 0
        segments.append({
            'segment': i + 1,
            'z_start': edges[i],
            'z_end': edges[i + 1],
            'count': int(count),
            'avg_diameter': avg_diam,
            'avg_volume': avg_vol,
        })
    return segments


def size_distribution_stats(spheres):
    diams = np.array([s['diameter'] for s in spheres])
    return {
        'count': len(diams),
        'mean': diams.mean(),
        'std': diams.std(),
        'median': np.median(diams),
        'cv_pct': (diams.std() / diams.mean()) * 100 if diams.mean() > 0 else 0,
        'q1': np.percentile(diams, 25),
        'q3': np.percentile(diams, 75),
        'min': diams.min(),
        'max': diams.max(),
        'd10': np.percentile(diams, 10),
        'd90': np.percentile(diams, 90),
        'span': (np.percentile(diams, 90) - np.percentile(diams, 10)) / np.median(diams),
    }


def plot_nnd(nnd, output_dir):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(nnd, bins=40, color='steelblue', edgecolor='white', alpha=0.8)
    ax.axvline(nnd.mean(), color='red', ls='--', label=f'Mean={nnd.mean():.2f} µm')
    ax.set_xlabel('Nearest Neighbor Distance (µm)')
    ax.set_ylabel('Count')
    ax.set_title('Nearest Neighbor Distance Distribution')
    ax.legend()
    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'nnd_histogram.png', dpi=200)
    plt.close()


def plot_diameter_vs_z(spheres, output_dir):
    zs = [s['cz'] for s in spheres]
    ds = [s['diameter'] for s in spheres]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(zs, ds, s=10, alpha=0.5, color='steelblue')
    ax.set_xlabel('Z position (µm)')
    ax.set_ylabel('Equivalent diameter (µm)')
    ax.set_title('Diameter vs Z Position')
    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'diameter_vs_z.png', dpi=200)
    plt.close()


def plot_size_distribution(spheres, output_dir):
    diams = [s['diameter'] for s in spheres]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(diams, bins=40, color='coral', edgecolor='white', alpha=0.8)
    ax.set_xlabel('Equivalent Diameter (µm)')
    ax.set_ylabel('Count')
    ax.set_title('Size Distribution')
    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'size_distribution.png', dpi=200)
    plt.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='spheres.csv from segmentation')
    parser.add_argument('--n-segments', type=int, default=10)
    parser.add_argument('--output-dir', default='./spatial_output/')
    args = parser.parse_args()

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    spheres = load_spheres(args.input)
    print(f"Loaded {len(spheres)} objects from {args.input}")

    nnd = nearest_neighbor_distances(spheres)
    stats = size_distribution_stats(spheres)
    segments = z_segment_stats(spheres, args.n_segments)

    print("\n=== Size Distribution ===")
    for k, v in stats.items():
        print(f"  {k:>10s}: {v:.3f}" if isinstance(v, float) else f"  {k:>10s}: {v}")

    print(f"\n=== Nearest Neighbor Distance ===")
    print(f"  Mean NND : {nnd.mean():.3f} µm")
    print(f"  Std NND  : {nnd.std():.3f} µm")
    print(f"  Min NND  : {nnd.min():.3f} µm")

    print(f"\n=== Z-Segment Statistics ({args.n_segments} segments) ===")
    for seg in segments:
        print(f"  Seg {seg['segment']:2d}: z=[{seg['z_start']:.1f}-{seg['z_end']:.1f}] "
              f"count={seg['count']:3d}, avg_diam={seg['avg_diameter']:.2f} µm")

    plot_nnd(nnd, outdir)
    plot_diameter_vs_z(spheres, outdir)
    plot_size_distribution(spheres, outdir)

    with open(outdir / 'spatial_stats.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['metric', 'value'])
        for k, v in stats.items():
            w.writerow([k, v])
        w.writerow(['mean_nnd_um', nnd.mean()])
        w.writerow(['std_nnd_um', nnd.std()])

    with open(outdir / 'z_segment_stats.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['segment', 'z_start_um', 'z_end_um', 'count', 'avg_diameter_um', 'avg_volume_um3'])
        for seg in segments:
            w.writerow([
                seg['segment'],
                seg['z_start'],
                seg['z_end'],
                seg['count'],
                seg['avg_diameter'],
                seg['avg_volume'],
            ])

    print(f"\nAll outputs saved to {outdir}/")
