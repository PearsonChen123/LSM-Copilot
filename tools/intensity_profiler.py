"""
Z-depth intensity profiler for fluorescence microscopy Z-stacks.

Usage:
    python intensity_profiler.py image.lsm --mode z-profile
    python intensity_profiler.py image.lsm --mode z-profile --correct
    python intensity_profiler.py image.lsm --mode roi --roi 100,100,300,300
"""
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path


def z_intensity_profile(data, voxel):
    """Compute mean and median intensity per Z-slice."""
    nz = data.shape[0]
    z_um = np.arange(nz) * voxel[0]
    means = np.array([data[z].mean() for z in range(nz)])
    medians = np.array([np.median(data[z]) for z in range(nz)])
    stds = np.array([data[z].std() for z in range(nz)])
    return z_um, means, medians, stds


def fit_attenuation(z_um, means):
    """Fit exponential decay: I(z) = A * exp(-mu * z) + C."""
    from scipy.optimize import curve_fit

    def exp_decay(z, A, mu, C):
        return A * np.exp(-mu * z) + C

    try:
        p0 = [means.max() - means.min(), 0.05, means.min()]
        popt, pcov = curve_fit(exp_decay, z_um, means, p0=p0, maxfev=5000)
        fitted = exp_decay(z_um, *popt)
        return popt, fitted
    except RuntimeError:
        return None, None


def correct_attenuation(data, z_um, popt):
    """Apply attenuation correction based on fitted parameters."""
    A, mu, C = popt
    corrected = data.copy()
    for z in range(data.shape[0]):
        factor = (A + C) / (A * np.exp(-mu * z_um[z]) + C)
        corrected[z] = data[z] * factor
    return corrected


def roi_intensity(data, voxel, roi):
    """Extract intensity within ROI across Z or T."""
    x1, y1, x2, y2 = roi
    nz = data.shape[0]
    z_um = np.arange(nz) * voxel[0]
    roi_data = data[:, y1:y2, x1:x2]
    means = np.array([roi_data[z].mean() for z in range(nz)])
    stds = np.array([roi_data[z].std() for z in range(nz)])
    intdens = np.array([roi_data[z].sum() for z in range(nz)])
    return z_um, means, stds, intdens


def plot_z_profile(z_um, means, medians, stds, fitted, popt, output_dir):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.fill_between(z_um, means - stds, means + stds, alpha=0.2, color='steelblue')
    ax.plot(z_um, means, 'o-', ms=2, color='steelblue', label='Mean')
    ax.plot(z_um, medians, 's-', ms=2, color='coral', label='Median')
    if fitted is not None:
        ax.plot(z_um, fitted, '--', color='black', lw=2,
                label=f'Fit: I₀={popt[0]:.1f}, µ={popt[1]:.4f}/µm')
    ax.set_xlabel('Z depth (µm)')
    ax.set_ylabel('Intensity')
    ax.set_title('Z-Depth Intensity Profile')
    ax.legend()
    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'z_intensity_profile.png', dpi=200)
    plt.close()
    print(f"Saved: {output_dir}/z_intensity_profile.png")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='Microscopy image file')
    parser.add_argument('--mode', choices=['z-profile', 'roi'], default='z-profile')
    parser.add_argument('--voxel', nargs=3, type=float, default=None)
    parser.add_argument('--roi', type=str, default=None, help='x1,y1,x2,y2')
    parser.add_argument('--correct', action='store_true', help='Apply attenuation correction')
    parser.add_argument('--output-dir', default='.', help='Output directory')
    args = parser.parse_args()

    from file_reader import load_image
    data, voxel, meta = load_image(args.input, args.voxel)
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    if args.mode == 'z-profile':
        z_um, means, medians, stds = z_intensity_profile(data, voxel)
        popt, fitted = fit_attenuation(z_um, means)
        if popt is not None:
            print(f"Attenuation fit: I₀={popt[0]:.2f}, µ={popt[1]:.5f}/µm, baseline={popt[2]:.2f}")
        plot_z_profile(z_um, means, medians, stds, fitted, popt, args.output_dir)

        if args.correct and popt is not None:
            import tifffile
            corrected = correct_attenuation(data, z_um, popt)
            out_path = Path(args.output_dir) / 'corrected.tif'
            tifffile.imwrite(str(out_path), corrected.astype(np.float32))
            print(f"Saved corrected stack: {out_path}")

    elif args.mode == 'roi':
        if args.roi is None:
            parser.error("--roi x1,y1,x2,y2 is required for ROI mode")
        roi = list(map(int, args.roi.split(',')))
        z_um, means, stds, intdens = roi_intensity(data, voxel, roi)
        print(f"ROI mean intensity range: {means.min():.1f} - {means.max():.1f}")
