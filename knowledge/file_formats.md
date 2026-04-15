# Microscopy File Formats

## Quick Reference

| Format | Extension | Python Reader | Auto-Metadata |
|--------|-----------|---------------|---------------|
| Zeiss LSM | `.lsm` | `tifffile` (built-in) | voxel size, channels |
| Zeiss CZI | `.czi` | `aicspylibczi` | full OME metadata |
| Leica LIF | `.lif` | `readlif` | voxel, series |
| OME-TIFF | `.ome.tif` | `tifffile` | OME-XML |
| Plain TIFF | `.tif` | `tifffile` | NONE |
| Nikon ND2 | `.nd2` | `nd2` | voxel, channels |
| MRC/MRC2000 | `.mrc`, `.mrcs`, `.map`, `.rec`, `.st` | `mrcfile` | voxel size (Å), cell dimensions |

For plain TIFF without metadata, you **must** ask the user for:
- Voxel size (Z, Y, X) in µm
- Dimension order (e.g., ZYX, ZCYX, TZYX)
- Number of channels

## Key Points

- `tifffile` handles most formats. Always try it first.
- For vendor-specific formats (CZI, LIF, ND2), search for the recommended Python reader if `tifffile` doesn't work.
- The `bioformats` / `python-bioformats` package can read almost anything but requires Java. Use as last resort.
- **MRC format** is common in cryo-EM and electron tomography, but also used for converted confocal/fluorescence stacks. The `mrcfile` package reads MRC2000 and older formats. Voxel sizes are stored in Ångströms in the header — divide by 10,000 to get µm. Extensions include `.mrc`, `.mrcs` (image stacks), `.map` (density maps), `.rec` (tomographic reconstructions), and `.st` (tilt series).
- **Bio-Formats** (Java) is the gold standard for format support. The Python wrapper `python-bioformats` or `pims.Bioformats` can be used if nothing else works — search for current installation instructions.
