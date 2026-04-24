"""
交互式 3D 液滴检测 GUI — 2D 切片浏览 + 3D 球体统计

用法:
    python gui_threshold.py image.lsm
    python gui_threshold.py image.tif --voxel 0.435 0.170 0.170

滑块:
    Z slice       — 切换 Z 层（仅切换视图，不重新计算）
    Otsu × factor — 阈值松紧
    BG kernel     — 背景校正窗口
    Min area      — 最小面积 (px)
    Min circ      — 最小圆度
    Min/Max d     — 直径过滤 (µm)

    拖动 Z slice 以外的滑块 → 自动重新计算全 3D

颜色: 每个 3D 球体分配唯一颜色
"""
import sys
import argparse
import numpy as np
import tifffile
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.patches import Circle, Ellipse
from matplotlib.colors import hsv_to_rgb
import csv, os, time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from scipy.ndimage import gaussian_filter, uniform_filter, label as ndi_label
from skimage.filters import threshold_otsu
from skimage.measure import marching_cubes, regionprops

N_WORKERS = max(1, os.cpu_count())
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('input', help='Input .lsm or .tif')
parser.add_argument('--voxel', nargs=3, type=float, default=None, metavar=('VZ','VY','VX'))
parser.add_argument(
    '--volume-alpha',
    type=float,
    default=None,
    help='Optional manual boundary alpha for surface-style volume: interior + alpha*boundary. No benchmark/GT auto-calibration is performed.',
)
args = parser.parse_args()

input_path = Path(args.input)
print(f"Loading {input_path.name}...")

with tifffile.TiffFile(str(input_path)) as f:
    if f.is_lsm and args.voxel is None:
        meta = f.lsm_metadata
        vz = meta['VoxelSizeZ'] * 1e6
        vy = meta['VoxelSizeY'] * 1e6
        vx = meta['VoxelSizeX'] * 1e6
    elif args.voxel:
        vz, vy, vx = args.voxel
    else:
        vz, vy, vx = 1.0, 1.0, 1.0
    raw = f.series[0].asarray().squeeze().astype(np.float32)

nz, ny, nx = raw.shape
voxel_vol = vz * vy * vx
print(f"Loaded: {raw.shape}, voxel: {vz:.3f}×{vy:.3f}×{vx:.3f} µm")

print("Pre-smoothing...")
smoothed = gaussian_filter(raw, sigma=(0.5, 1.0, 1.0))
mip_yz = raw.min(axis=2)
print("Ready.")


def make_colors(n):
    """生成 n 个视觉区分度高的颜色"""
    if n == 0:
        return []
    hues = np.linspace(0, 1, n, endpoint=False)
    np.random.seed(42)
    hues = (hues + np.random.rand()) % 1.0
    return [hsv_to_rgb([h, 0.9, 0.95]) for h in hues]


def component_boundary_counts(labels):
    """Return per-label interior and boundary voxel counts for 3D labels."""
    foreground = labels > 0
    if not foreground.any():
        return np.array([0]), np.array([0])
    padded = np.pad(labels, 1, mode='constant', constant_values=0)
    center = padded[1:-1, 1:-1, 1:-1]
    same_neighbor = (
        (padded[:-2, 1:-1, 1:-1] == center)
        & (padded[2:, 1:-1, 1:-1] == center)
        & (padded[1:-1, :-2, 1:-1] == center)
        & (padded[1:-1, 2:, 1:-1] == center)
        & (padded[1:-1, 1:-1, :-2] == center)
        & (padded[1:-1, 1:-1, 2:] == center)
    )
    interior = foreground & same_neighbor
    boundary = foreground & ~same_neighbor
    max_label = int(labels.max())
    interior_counts = np.bincount(labels[interior].ravel(), minlength=max_label + 1)
    boundary_counts = np.bincount(labels[boundary].ravel(), minlength=max_label + 1)
    return interior_counts, boundary_counts


def mesh_volume_from_mask(mask):
    """Compute non-GT surface volume directly from a 3D binary object mask."""
    if not mask.any():
        return 0.0
    padded = np.pad(mask.astype(np.float32), 1, mode='constant', constant_values=0)
    try:
        vertices, faces, _, _ = marching_cubes(padded, level=0.5, spacing=(vz, vy, vx))
    except Exception:
        return float(mask.sum() * voxel_vol)
    triangles = vertices[faces]
    signed = np.einsum('ij,ij->i', np.cross(triangles[:, 0], triangles[:, 1]), triangles[:, 2])
    return float(abs(signed.sum()) / 6.0)


# ====== 3D Detection Core (multi-core) ======

def _otsu_bg(args):
    sl, factor = args
    pos = sl[sl > 0]
    if len(pos) < 100:
        return None
    try:
        T = threshold_otsu(pos)
    except ValueError:
        return None
    return sl > (T * factor)


def _otsu_direct(args):
    sl, factor, inv = args
    if sl.std() < 1.0:
        return None
    try:
        T = threshold_otsu(sl)
    except ValueError:
        return None
    return sl > (T * factor) if inv else sl < (T * factor)


class Detector:
    def __init__(self):
        self.spheres = []
        self.labels_3d = None
        self.sphere_colors = {}
        self._bg_cache_key = None
        self._bg_cache = None

    def run(self, factor, bg_kernel, min_area, min_circ, min_d, max_d,
            z_start=0, z_end=None, invert=False):
        if z_end is None:
            z_end = nz
        z_start = max(0, min(int(z_start), nz - 1))
        z_end = max(z_start + 1, min(int(z_end), nz))
        self.z_start = z_start
        self.z_end = z_end
        t0 = time.time()
        mode = "bright" if invert else "dark"
        print(f"  [{N_WORKERS} cores] Z {z_start}-{z_end} ({mode})...",
              end=' ', flush=True)

        bg_key = int(bg_kernel)
        binary = np.zeros(smoothed.shape, dtype=bool)

        if bg_key > 5:
            if bg_key != self._bg_cache_key:
                self._bg_cache = uniform_filter(smoothed, size=(1, bg_key, bg_key))
                self._bg_cache_key = bg_key
            if invert:
                contrast = np.clip(smoothed - self._bg_cache, 0, None)
            else:
                contrast = np.clip(self._bg_cache - smoothed, 0, None)

            tasks = [(contrast[z], factor) for z in range(z_start, z_end)]
            with ThreadPoolExecutor(max_workers=N_WORKERS) as pool:
                results = list(pool.map(_otsu_bg, tasks))
            for i, r in enumerate(results):
                if r is not None:
                    binary[z_start + i] = r
        else:
            self._bg_cache_key = None
            tasks = [(smoothed[z], factor, invert) for z in range(z_start, z_end)]
            with ThreadPoolExecutor(max_workers=N_WORKERS) as pool:
                results = list(pool.map(_otsu_direct, tasks))
            for i, r in enumerate(results):
                if r is not None:
                    binary[z_start + i] = r

        labels, n_obj = ndi_label(binary)
        self.labels_3d = labels
        interior_counts, boundary_counts = component_boundary_counts(labels)
        volume_alpha_source = 'manual_alpha' if args.volume_alpha is not None else 'not_used_mesh_volume'
        raw_volume_alpha = 1.0 if args.volume_alpha is None else float(args.volume_alpha)
        volume_alpha = float(np.clip(raw_volume_alpha, 0.25, 2.50))

        props = regionprops(labels, intensity_image=raw)
        self.spheres = []

        for p in props:
            if p.area < min_area:
                continue

            bb = p.bbox
            label_id = int(p.label)
            filled_vol_um3 = p.area * voxel_vol
            interior_voxels = int(interior_counts[label_id])
            boundary_voxels = int(boundary_counts[label_id])
            boundary_alpha_0_5_vol_um3 = (interior_voxels + 0.5 * boundary_voxels) * voxel_vol
            sub = labels[bb[0]:bb[3], bb[1]:bb[4], bb[2]:bb[5]] == p.label
            mesh_vol_um3 = mesh_volume_from_mask(sub)
            if args.volume_alpha is None:
                vol_um3 = mesh_vol_um3
                volume_mode = 'surface_mesh_volume_um3'
            else:
                vol_um3 = (interior_voxels + volume_alpha * boundary_voxels) * voxel_vol
                volume_mode = 'manual_boundary_alpha_volume_um3'
            r_um = (3.0 * vol_um3 / (4.0 * np.pi)) ** (1.0 / 3.0)
            d_um = 2 * r_um
            dz_bb = (bb[3] - bb[0]) * vz
            dy_bb = (bb[4] - bb[1]) * vy
            dx_bb = (bb[5] - bb[2]) * vx
            bb_max = max(dz_bb, dy_bb, dx_bb)
            bb_min = min(dz_bb, dy_bb, dx_bb) + 1e-8
            aspect = bb_max / bb_min

            sub = labels[bb[0]:bb[3], bb[1]:bb[4], bb[2]:bb[5]]
            n_slices_in = int((sub == p.label).any(axis=(1, 2)).sum())

            if min_circ > 0 and aspect > (1.0 / min_circ + 1):
                continue
            if d_um < min_d or d_um > max_d:
                continue
            if bb[0] <= z_start or bb[3] >= z_end or bb[1] == 0 or bb[4] >= ny or bb[2] == 0 or bb[5] >= nx:
                continue

            cz, cy, cx = p.centroid
            self.spheres.append({
                'label': p.label,
                'cz': cz, 'cy': cy, 'cx': cx,
                'cz_um': cz * vz, 'cy_um': cy * vy, 'cx_um': cx * vx,
                'diameter': d_um,
                'radius': r_um,
                'volume': vol_um3,
                'volume_mode': volume_mode,
                'surface_mesh_volume_um3': mesh_vol_um3,
                'voxel_filled_volume_um3': filled_vol_um3,
                'boundary_alpha_0_5_volume_um3': boundary_alpha_0_5_vol_um3,
                'volume_alpha': volume_alpha,
                'volume_alpha_source': volume_alpha_source,
                'benchmark_used_for_volume_calibration': False,
                'z_start': bb[0], 'z_end': bb[3] - 1,
                'n_slices': n_slices_in,
                'intensity': p.intensity_mean,
                'aspect': aspect,
            })

        colors = make_colors(len(self.spheres))
        self.sphere_colors = {}
        for i, s in enumerate(self.spheres):
            self.sphere_colors[s['label']] = colors[i]

        print(
            f"{len(self.spheres)} spheres ({time.time()-t0:.1f}s, "
            f"volume mode={self.spheres[0]['volume_mode'] if self.spheres else 'none'}, "
            f"benchmark_calibration=false)"
        )

    def get_slice_circles(self, zi):
        circles = []
        zi_um = zi * vz
        for s in self.spheres:
            if s['z_start'] > zi or s['z_end'] < zi:
                continue
            dz_um = abs(zi_um - s['cz_um'])
            r_um = s['radius']
            if dz_um >= r_um:
                continue
            r_cross = np.sqrt(r_um ** 2 - dz_um ** 2)
            r_px = r_cross / vy
            circles.append({
                'cx': s['cx'], 'cy': s['cy'], 'r_px': r_px,
                'color': self.sphere_colors[s['label']],
                'sphere': s,
                'is_center': abs(zi - s['cz']) < 1.5,
            })
        return circles


det = Detector()

# ====== GUI ======
fig = plt.figure(figsize=(32, 13))
gs = fig.add_gridspec(2, 12, height_ratios=[3, 1], hspace=0.3,
                      left=0.03, right=0.97, top=0.93, bottom=0.26)

ax_slice = fig.add_subplot(gs[0, 0:4])
ax_zprof = fig.add_subplot(gs[0, 4:8])
ax_stats = fig.add_subplot(gs[0, 8:12])
ax_hist = fig.add_subplot(gs[1, 0:3])
ax_avgvol = fig.add_subplot(gs[1, 3:6])
ax_zdist = fig.add_subplot(gs[1, 6:9])
ax_info = fig.add_subplot(gs[1, 9:12])

im_slice = ax_slice.imshow(raw[nz//2], cmap='gray')
ax_slice.axis('off')

im_zprof = ax_zprof.imshow(mip_yz, cmap='gray', aspect=vz/vy)
ax_zprof.set_title('YZ Min-IP')
ax_zprof.axis('off')

slider_y = [0.21, 0.19, 0.17, 0.15, 0.13, 0.11, 0.09, 0.07, 0.05]
sliders = {}
sdefs = [
    ('Z slice',      0, nz-1, nz//2, 1),
    ('Z start',      0, nz-1, int(nz * 0.10), 1),
    ('Z end',        0, nz-1, int(nz * 0.95), 1),
    ('Invert 0=dark 1=bright', 0, 1, 0, 1),
    ('Otsu x fact',  0.3, 1.2, 1.0, None),
    ('BG kernel',    0, 200, 70, 5),
    ('Min area',     5, 500, 30, 5),
    ('Min d (um)',   0.0, 5.0, 0.5, None),
    ('Max d (um)',   5.0, 80.0, 50.0, None),
]
for i, (name, lo, hi, init, step) in enumerate(sdefs):
    ax_s = fig.add_axes([0.08, slider_y[i], 0.35, 0.018])
    kw = dict(valinit=init)
    if step is not None:
        kw['valstep'] = step
    sliders[name] = Slider(ax_s, name, lo, hi, **kw)

patches = []
zline = None


def draw_slice(zi):
    global patches, zline
    img = raw[zi]
    im_slice.set_data(img)
    im_slice.set_clim(img.min(), img.max())

    for p in patches:
        p.remove()
    patches = []

    circles = det.get_slice_circles(zi)
    for c in circles:
        lw = 1.5 if c['is_center'] else 0.7
        ls = '-' if c['is_center'] else '--'
        patch = Circle((c['cx'], c['cy']), c['r_px'], fill=False,
                        edgecolor=c['color'], linewidth=lw, linestyle=ls)
        ax_slice.add_patch(patch)
        patches.append(patch)

        if c['is_center']:
            s = c['sphere']
            txt = ax_slice.text(c['cx'] + c['r_px'] + 3, c['cy'],
                                f"#{det.spheres.index(s)+1}",
                                color=c['color'], fontsize=7, fontweight='bold',
                                va='center')
            patches.append(txt)

    n_visible = len(circles)
    n_center = sum(1 for c in circles if c['is_center'])
    ax_slice.set_title(f'Z={zi} ({zi*vz:.1f}µm) — {n_visible} visible, '
                       f'{n_center} centered here', fontsize=10)

    if zline is not None:
        zline.remove()
    zline = ax_zprof.axhline(y=zi, color='yellow', linewidth=1, alpha=0.8)

    fig.canvas.draw_idle()


def draw_zprofile():
    ax_zprof.clear()
    ax_zprof.imshow(mip_yz, cmap='gray', aspect=vz/vy)

    z_start = int(sliders['Z start'].val)
    z_end = int(sliders['Z end'].val)
    ax_zprof.axhline(y=z_start, color='lime', linewidth=1, alpha=0.6, linestyle='--')
    ax_zprof.axhline(y=z_end, color='red', linewidth=1, alpha=0.6, linestyle='--')

    for s in det.spheres:
        color = det.sphere_colors[s['label']]
        cy_px = s['cy']
        cz_px = s['cz']
        r_y_px = s['radius'] / vy
        r_z_px = s['radius'] / vz
        ax_zprof.add_patch(Ellipse((cy_px, cz_px), 2 * r_y_px, 2 * r_z_px,
                                    fill=False, edgecolor=color, linewidth=0.6))
    ax_zprof.set_title(f'YZ Min-IP ({len(det.spheres)} spheres)')
    ax_zprof.axis('off')


def draw_stats():
    """Diameter vs Z position scatter plot."""
    ax_stats.clear()
    if not det.spheres:
        ax_stats.text(0.5, 0.5, 'No spheres', ha='center', va='center',
                      fontsize=14, transform=ax_stats.transAxes)
        ax_stats.set_title('Diameter vs Z')
        return

    zs = np.array([s['cz_um'] for s in det.spheres])
    ds = np.array([s['diameter'] for s in det.spheres])
    ax_stats.scatter(zs, ds, s=8, c='black', alpha=0.5, edgecolors='none')
    ax_stats.set_xlabel('Position Z [µm]', fontsize=9)
    ax_stats.set_ylabel('Equivalent diameter [µm]', fontsize=9)
    ax_stats.set_title(f'Diameter vs Z ({len(det.spheres)} spheres)', fontsize=10)
    ax_stats.grid(True, alpha=0.3)
    ax_stats.set_xlim(left=0)
    ax_stats.set_ylim(bottom=0)


N_SEGMENTS = 10

def draw_histograms():
    ax_hist.clear()
    ax_avgvol.clear()
    ax_zdist.clear()
    ax_info.clear()

    if not det.spheres:
        for ax in [ax_hist, ax_avgvol, ax_zdist, ax_info]:
            ax.set_title('')
        ax_info.axis('off')
        return

    z_start_um = det.z_start * vz
    z_end_um = det.z_end * vz
    seg_edges = np.linspace(z_start_um, z_end_um, N_SEGMENTS + 1)
    seg_mids = 0.5 * (seg_edges[:-1] + seg_edges[1:])
    seg_width = seg_edges[1] - seg_edges[0]

    zs = np.array([s['cz_um'] for s in det.spheres])
    ds_arr = np.array([s['diameter'] for s in det.spheres])
    counts, _ = np.histogram(zs, bins=seg_edges)
    seg_idx = np.digitize(zs, seg_edges) - 1
    seg_idx = np.clip(seg_idx, 0, N_SEGMENTS - 1)
    avg_diam = np.zeros(N_SEGMENTS)
    for i in range(N_SEGMENTS):
        mask = seg_idx == i
        if mask.any():
            avg_diam[i] = ds_arr[mask].mean()

    colors_bar = plt.cm.viridis(np.linspace(0.2, 0.9, N_SEGMENTS))
    bars = ax_hist.bar(seg_mids, counts, width=seg_width * 0.9,
                       color=colors_bar, edgecolor='white', linewidth=0.5)
    for bar, c in zip(bars, counts):
        if c > 0:
            ax_hist.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                         str(c), ha='center', va='bottom', fontsize=6, fontweight='bold')
    ax_hist.set_xlabel('Z position (µm)', fontsize=9)
    ax_hist.set_ylabel('Sphere count', fontsize=9)
    ax_hist.set_title(f'Sphere count per segment ({N_SEGMENTS})', fontsize=10)
    ax_hist.set_xlim(z_start_um, z_end_um)

    colors_diam = plt.cm.magma(np.linspace(0.2, 0.85, N_SEGMENTS))
    bars_v = ax_avgvol.bar(seg_mids, avg_diam, width=seg_width * 0.9,
                           color=colors_diam, edgecolor='white', linewidth=0.5)
    for bar, av, c in zip(bars_v, avg_diam, counts):
        if c > 0:
            ax_avgvol.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                           f'{av:.1f}', ha='center', va='bottom',
                           fontsize=6, fontweight='bold')
    ax_avgvol.set_xlabel('Z position (µm)', fontsize=9)
    ax_avgvol.set_ylabel('Avg diameter (µm)', fontsize=9)
    ax_avgvol.set_title(f'Avg diameter per segment ({N_SEGMENTS})', fontsize=10)
    ax_avgvol.set_xlim(z_start_um, z_end_um)

    ax_zdist.hist(ds_arr, bins=30, color='teal', edgecolor='white', alpha=0.8)
    ax_zdist.axvline(np.median(ds_arr), color='red', ls='--',
                     label=f'median={np.median(ds_arr):.1f}µm')
    ax_zdist.set_xlabel('Diameter (µm)', fontsize=9)
    ax_zdist.set_title('Size distribution', fontsize=10)
    ax_zdist.legend(fontsize=8)

    seg_labels = [f"{seg_edges[i]:.1f}-{seg_edges[i+1]:.1f}" for i in range(N_SEGMENTS)]
    summary = (
        f"Total spheres:  {len(det.spheres)}\n"
        f"Diameter range: {ds_arr.min():.1f} – {ds_arr.max():.1f} µm\n"
        f"  mean={ds_arr.mean():.1f}  median={np.median(ds_arr):.1f} µm\n"
        f"Z range:        {zs.min():.1f} – {zs.max():.1f} µm\n"
        f"Segment size:   {seg_width:.2f} µm\n"
        f"{'─'*46}\n"
        f" {'#':>2}  {'Z range (µm)':>14}  {'count':>5}  {'avg diam(µm)':>12}\n"
        f"{'─'*46}\n"
    )
    for i in range(N_SEGMENTS):
        av_str = f"{avg_diam[i]:.1f}" if counts[i] > 0 else "—"
        summary += f" {i+1:>2}. {seg_labels[i]:>14}  {counts[i]:>5}  {av_str:>12}\n"

    ax_info.text(0.02, 0.98, summary, transform=ax_info.transAxes,
                 fontsize=7, va='top', fontfamily='monospace',
                 bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
    ax_info.set_title('Summary & Segment Table', fontsize=10)
    ax_info.axis('off')


def recompute(val=None):
    factor = sliders['Otsu x fact'].val
    bg_kernel = sliders['BG kernel'].val
    min_area = int(sliders['Min area'].val)
    min_d = sliders['Min d (um)'].val
    max_d = sliders['Max d (um)'].val
    z_start = int(sliders['Z start'].val)
    z_end = int(sliders['Z end'].val)
    invert = int(sliders['Invert 0=dark 1=bright'].val) == 1

    det.run(factor, bg_kernel, min_area, 0.0, min_d, max_d, z_start, z_end, invert)
    draw_zprofile()
    draw_stats()
    draw_histograms()
    zi = int(sliders['Z slice'].val)
    zi = max(z_start, min(zi, z_end - 1))
    draw_slice(zi)


def on_z_change(val):
    draw_slice(int(val))

sliders['Z slice'].on_changed(on_z_change)
for name in ['Z start', 'Z end', 'Invert 0=dark 1=bright', 'Otsu x fact',
             'BG kernel', 'Min area', 'Min d (um)', 'Max d (um)']:
    sliders[name].on_changed(recompute)

def _seg_data():
    """计算分段统计数据，供保存和绘图复用"""
    z_start_um = det.z_start * vz
    z_end_um = det.z_end * vz
    seg_edges = np.linspace(z_start_um, z_end_um, N_SEGMENTS + 1)
    seg_mids = 0.5 * (seg_edges[:-1] + seg_edges[1:])
    seg_width = seg_edges[1] - seg_edges[0]
    zs = np.array([s['cz_um'] for s in det.spheres])
    ds = np.array([s['diameter'] for s in det.spheres])
    counts, _ = np.histogram(zs, bins=seg_edges)
    seg_idx = np.clip(np.digitize(zs, seg_edges) - 1, 0, N_SEGMENTS - 1)
    avg_diam = np.zeros(N_SEGMENTS)
    for i in range(N_SEGMENTS):
        mask = seg_idx == i
        if mask.any():
            avg_diam[i] = ds[mask].mean()
    return dict(seg_edges=seg_edges, seg_mids=seg_mids, seg_width=seg_width,
                zs=zs, ds=ds, counts=counts, avg_diam=avg_diam)


def save_all(event=None):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = input_path.parent / f'output_{ts}'
    out_dir.mkdir(exist_ok=True)
    dpi = 200
    print(f"\nSaving to {out_dir} ...")

    if not det.spheres:
        print("  No spheres to save.")
        return

    zs = np.array([s['cz_um'] for s in det.spheres])
    ds = np.array([s['diameter'] for s in det.spheres])
    sd = _seg_data()

    # ========== CSV ==========

    # 1) spheres.csv
    with open(out_dir / 'spheres.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['id', 'cz_um', 'cy_um', 'cx_um', 'diameter_um', 'radius_um',
                     'volume_um3', 'volume_mode', 'surface_mesh_volume_um3',
                     'voxel_filled_volume_um3',
                     'boundary_alpha_0_5_volume_um3', 'volume_alpha',
                     'volume_alpha_source', 'benchmark_used_for_volume_calibration',
                     'z_start', 'z_end', 'n_slices', 'intensity', 'aspect'])
        for i, s in enumerate(det.spheres):
            w.writerow([i + 1, f"{s['cz_um']:.3f}", f"{s['cy_um']:.3f}",
                        f"{s['cx_um']:.3f}", f"{s['diameter']:.3f}",
                        f"{s['radius']:.3f}", f"{s['volume']:.3f}",
                        s['volume_mode'], f"{s['surface_mesh_volume_um3']:.3f}",
                        f"{s['voxel_filled_volume_um3']:.3f}",
                        f"{s['boundary_alpha_0_5_volume_um3']:.3f}",
                        f"{s['volume_alpha']:.6f}", s['volume_alpha_source'],
                        s['benchmark_used_for_volume_calibration'],
                        s['z_start'], s['z_end'], s['n_slices'],
                        f"{s['intensity']:.2f}", f"{s['aspect']:.3f}"])
    print(f"  spheres.csv ({len(det.spheres)} rows)")

    # 2) diameter_vs_z.csv
    with open(out_dir / 'diameter_vs_z.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['id', 'position_z_um', 'volume_um3', 'diameter_um',
                    'volume_mode', 'volume_alpha', 'volume_alpha_source',
                    'benchmark_used_for_volume_calibration'])
        for i, s in enumerate(det.spheres):
            w.writerow([i + 1, f"{s['cz_um']:.3f}", f"{s['volume']:.3f}",
                        f"{s['diameter']:.3f}", s['volume_mode'],
                        f"{s['volume_alpha']:.6f}", s['volume_alpha_source'],
                        s['benchmark_used_for_volume_calibration']])
    print(f"  diameter_vs_z.csv ({len(det.spheres)} rows)")

    # 3) segments.csv
    with open(out_dir / 'segments.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['segment', 'z_start_um', 'z_end_um', 'count', 'avg_diameter_um'])
        for i in range(N_SEGMENTS):
            w.writerow([i + 1, f"{sd['seg_edges'][i]:.2f}",
                        f"{sd['seg_edges'][i+1]:.2f}", sd['counts'][i],
                        f"{sd['avg_diam'][i]:.3f}" if sd['counts'][i] > 0 else ''])
    print(f"  segments.csv ({N_SEGMENTS} rows)")

    # ========== PNG: 独立绘制 ==========

    # 1) slice_view.png
    zi = int(sliders['Z slice'].val)
    f1, a1 = plt.subplots(figsize=(8, 8))
    a1.imshow(raw[zi], cmap='gray')
    for c in det.get_slice_circles(zi):
        lw = 1.5 if c['is_center'] else 0.7
        ls = '-' if c['is_center'] else '--'
        a1.add_patch(Circle((c['cx'], c['cy']), c['r_px'], fill=False,
                             edgecolor=c['color'], linewidth=lw, linestyle=ls))
    a1.set_title(f'Z={zi} ({zi*vz:.1f} µm)', fontsize=12)
    a1.axis('off')
    f1.tight_layout()
    f1.savefig(out_dir / 'slice_view.png', dpi=dpi, facecolor='white')
    plt.close(f1)
    print("  slice_view.png")

    # 2) yz_minip.png
    f2, a2 = plt.subplots(figsize=(8, 6))
    a2.imshow(mip_yz, cmap='gray', aspect=vz/vy)
    a2.axhline(y=det.z_start, color='lime', lw=1, alpha=0.6, ls='--')
    a2.axhline(y=det.z_end, color='red', lw=1, alpha=0.6, ls='--')
    for s in det.spheres:
        color = det.sphere_colors[s['label']]
        a2.add_patch(Ellipse((s['cy'], s['cz']), 2 * s['radius'] / vy,
                              2 * s['radius'] / vz, fill=False,
                              edgecolor=color, linewidth=0.6))
    a2.set_title(f'YZ Min-IP ({len(det.spheres)} spheres)', fontsize=12)
    a2.axis('off')
    f2.tight_layout()
    f2.savefig(out_dir / 'yz_minip.png', dpi=dpi, facecolor='white')
    plt.close(f2)
    print("  yz_minip.png")

    # 3) diameter_vs_z.png
    f3, a3 = plt.subplots(figsize=(8, 5))
    a3.scatter(zs, ds, s=10, c='black', alpha=0.5, edgecolors='none')
    a3.set_xlabel('Position Z [µm]', fontsize=11)
    a3.set_ylabel('Equivalent diameter [µm]', fontsize=11)
    a3.set_title(f'Diameter vs Z ({len(det.spheres)} spheres)', fontsize=12)
    a3.grid(True, alpha=0.3)
    a3.set_xlim(left=0)
    a3.set_ylim(bottom=0)
    f3.tight_layout()
    f3.savefig(out_dir / 'diameter_vs_z.png', dpi=dpi, facecolor='white')
    plt.close(f3)
    print("  diameter_vs_z.png")

    # 4) count_per_segment.png
    f4, a4 = plt.subplots(figsize=(8, 4))
    colors_bar = plt.cm.viridis(np.linspace(0.2, 0.9, N_SEGMENTS))
    bars = a4.bar(sd['seg_mids'], sd['counts'], width=sd['seg_width'] * 0.9,
                  color=colors_bar, edgecolor='white', linewidth=0.5)
    for bar, c in zip(bars, sd['counts']):
        if c > 0:
            a4.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(c), ha='center', va='bottom', fontsize=8, fontweight='bold')
    a4.set_xlabel('Z position (µm)', fontsize=11)
    a4.set_ylabel('Sphere count', fontsize=11)
    a4.set_title(f'Sphere count per segment ({N_SEGMENTS})', fontsize=12)
    a4.set_xlim(sd['seg_edges'][0], sd['seg_edges'][-1])
    f4.tight_layout()
    f4.savefig(out_dir / 'count_per_segment.png', dpi=dpi, facecolor='white')
    plt.close(f4)
    print("  count_per_segment.png")

    # 5) avg_diameter_per_segment.png
    f5, a5 = plt.subplots(figsize=(8, 4))
    colors_diam = plt.cm.magma(np.linspace(0.2, 0.85, N_SEGMENTS))
    bars_v = a5.bar(sd['seg_mids'], sd['avg_diam'], width=sd['seg_width'] * 0.9,
                    color=colors_diam, edgecolor='white', linewidth=0.5)
    for bar, av, c in zip(bars_v, sd['avg_diam'], sd['counts']):
        if c > 0:
            a5.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                    f'{av:.1f}', ha='center', va='bottom', fontsize=8, fontweight='bold')
    a5.set_xlabel('Z position (µm)', fontsize=11)
    a5.set_ylabel('Avg diameter (µm)', fontsize=11)
    a5.set_title(f'Avg diameter per segment ({N_SEGMENTS})', fontsize=12)
    a5.set_xlim(sd['seg_edges'][0], sd['seg_edges'][-1])
    f5.tight_layout()
    f5.savefig(out_dir / 'avg_diameter_per_segment.png', dpi=dpi, facecolor='white')
    plt.close(f5)
    print("  avg_diameter_per_segment.png")

    # 6) diameter_distribution.png
    f6, a6 = plt.subplots(figsize=(8, 4))
    a6.hist(ds, bins=30, color='teal', edgecolor='white', alpha=0.8)
    a6.axvline(np.median(ds), color='red', ls='--',
               label=f'median={np.median(ds):.1f} µm')
    a6.set_xlabel('Diameter (µm)', fontsize=11)
    a6.set_ylabel('Count', fontsize=11)
    a6.set_title('Size distribution', fontsize=12)
    a6.legend(fontsize=10)
    f6.tight_layout()
    f6.savefig(out_dir / 'diameter_distribution.png', dpi=dpi, facecolor='white')
    plt.close(f6)
    print("  diameter_distribution.png")

    # 7) full_gui.png
    fig.savefig(out_dir / 'full_gui.png', dpi=120, facecolor='white', edgecolor='none')
    print(f"  full_gui.png")
    print(f"Done! All files saved to {out_dir}")


ax_btn = fig.add_axes([0.46, 0.07, 0.08, 0.035])
btn_save = Button(ax_btn, 'Save All', color='lightyellow', hovercolor='gold')
btn_save.on_clicked(save_all)

recompute()

fig.suptitle('3D Sphere Detection — solid=center slice, dashed=passing through',
             fontsize=12, fontweight='bold')
print("GUI ready.")
plt.show()
