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

For plain TIFF without metadata, you **must** ask the user for:
- Voxel size (Z, Y, X) in µm
- Dimension order (e.g., ZYX, ZCYX, TZYX)
- Number of channels

## Key Points

- `tifffile` handles most formats. Always try it first.
- For vendor-specific formats (CZI, LIF, ND2), search for the recommended Python reader if `tifffile` doesn't work.
- The `bioformats` / `python-bioformats` package can read almost anything but requires Java. Use as last resort.
- **Bio-Formats** (Java) is the gold standard for format support. The Python wrapper `python-bioformats` or `pims.Bioformats` can be used if nothing else works — search for current installation instructions.
