"""
Colocalization analyzer for multi-channel fluorescence images.

Usage:
    python coloc_analyzer.py image.lsm --ch1 0 --ch2 1
    python coloc_analyzer.py image.tif --ch1 0 --ch2 1 --voxel 0.44 0.17 0.17
"""
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path


def pearson_coefficient(ch1, ch2):
    c1 = ch1.ravel().astype(np.float64)
    c2 = ch2.ravel().astype(np.float64)
    c1 -= c1.mean()
    c2 -= c2.mean()
    num = np.sum(c1 * c2)
    denom = np.sqrt(np.sum(c1**2) * np.sum(c2**2))
    return num / denom if denom > 0 else 0.0


def manders_coefficients(ch1, ch2, t1=0, t2=0):
    mask1 = ch1 > t1
    mask2 = ch2 > t2
    m1 = ch1[mask2].sum() / ch1[mask1].sum() if ch1[mask1].sum() > 0 else 0.0
    m2 = ch2[mask1].sum() / ch2[mask2].sum() if ch2[mask2].sum() > 0 else 0.0
    return m1, m2


def li_icq(ch1, ch2):
    """Li's Intensity Correlation Quotient."""
    c1 = ch1.ravel().astype(np.float64)
    c2 = ch2.ravel().astype(np.float64)
    diff1 = c1 - c1.mean()
    diff2 = c2 - c2.mean()
    product = diff1 * diff2
    n_positive = np.sum(product > 0)
    return n_positive / len(product) - 0.5


def costes_threshold(ch1, ch2):
    """Costes automatic threshold: find threshold where PCC of below-threshold pixels = 0."""
    from skimage.filters import threshold_otsu
    t1 = threshold_otsu(ch1)
    t2 = threshold_otsu(ch2)
    return t1, t2


def scatter_plot(ch1, ch2, output_path, subsample=50000):
    c1 = ch1.ravel()
    c2 = ch2.ravel()
    if len(c1) > subsample:
        idx = np.random.choice(len(c1), subsample, replace=False)
        c1, c2 = c1[idx], c2[idx]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(c1, c2, s=0.5, alpha=0.1, color='steelblue')
    ax.set_xlabel('Channel 1 Intensity')
    ax.set_ylabel('Channel 2 Intensity')
    ax.set_title('Colocalization Scatter Plot')
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def merged_overlay(ch1, ch2, z_slice, output_path):
    """Create RGB merge: ch1=green, ch2=red, overlap=yellow."""
    c1 = ch1[z_slice].astype(np.float32)
    c2 = ch2[z_slice].astype(np.float32)
    c1 = (c1 - c1.min()) / (c1.max() - c1.min() + 1e-8)
    c2 = (c2 - c2.min()) / (c2.max() - c2.min() + 1e-8)
    rgb = np.stack([c2, c1, np.zeros_like(c1)], axis=-1)
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(rgb)
    ax.set_title(f'Merged Overlay (Z={z_slice}): Green=Ch1, Red=Ch2')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='Multi-channel microscopy image')
    parser.add_argument('--ch1', type=int, default=0, help='Channel 1 index')
    parser.add_argument('--ch2', type=int, default=1, help='Channel 2 index')
    parser.add_argument('--voxel', nargs=3, type=float, default=None)
    parser.add_argument('--threshold', default='auto', help='auto or manual t1,t2')
    parser.add_argument('--output-dir', default='.', help='Output directory')
    args = parser.parse_args()

    import tifffile
    with tifffile.TiffFile(args.input) as f:
        raw = f.series[0].asarray().squeeze().astype(np.float32)

    if raw.ndim < 4:
        print(f"Error: Image has shape {raw.shape}, need ≥2 channels (4D: Z×C×Y×X)")
        exit(1)

    ch1_data = raw[:, args.ch1]
    ch2_data = raw[:, args.ch2]

    if args.threshold == 'auto':
        t1, t2 = costes_threshold(ch1_data, ch2_data)
    else:
        t1, t2 = map(float, args.threshold.split(','))

    pcc = pearson_coefficient(ch1_data, ch2_data)
    m1, m2 = manders_coefficients(ch1_data, ch2_data, t1, t2)
    icq = li_icq(ch1_data, ch2_data)

    print("=" * 50)
    print("  Colocalization Results")
    print("=" * 50)
    print(f"  Pearson's r   : {pcc:.4f}")
    print(f"  Manders' M1   : {m1:.4f} (Ch1 in Ch2)")
    print(f"  Manders' M2   : {m2:.4f} (Ch2 in Ch1)")
    print(f"  Li's ICQ      : {icq:.4f}")
    print(f"  Thresholds    : Ch1={t1:.1f}, Ch2={t2:.1f}")
    print("=" * 50)

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    scatter_plot(ch1_data, ch2_data, outdir / 'coloc_scatter.png')
    merged_overlay(ch1_data, ch2_data, ch1_data.shape[0] // 2, outdir / 'coloc_merged.png')
    print(f"Figures saved to {outdir}/")
