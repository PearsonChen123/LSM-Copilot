# Intensity Analysis: Guiding Principles

## Common Questions Researchers Ask

- "Why is the bottom of my Z-stack darker?" → Laser attenuation with depth
- "Is the fluorescence quantitative?" → Depends on imaging conditions, saturation, photobleaching
- "How do I compare intensity between samples?" → Need consistent imaging settings + proper normalization

## What to Watch Out For

- **Laser attenuation**: Signal decays exponentially with Z-depth due to scattering/absorption. Always plot intensity vs Z first.
- **Photobleaching**: In time-lapse, signal decays over frames. Plot intensity vs time.
- **Saturation**: If max intensity = 255 (8-bit) or 4095 (12-bit), data is clipped. Cannot be corrected.
- **Background**: Varies spatially and with depth. Subtract before quantifying.

## When to Search

- User needs FRET analysis → search for FRET efficiency calculation, donor/acceptor correction
- User needs FLIM → search for PhasorPy or FLIMPA
- User needs ratiometric imaging → sample-specific, search for the specific probe/assay
- Unusual correction methods → search for latest approaches

## Key Output

Always provide: intensity profile plot, background level estimate, whether correction is needed, corrected data if applicable.
