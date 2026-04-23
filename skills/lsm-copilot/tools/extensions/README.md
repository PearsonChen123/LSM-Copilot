# Extension Adapters

This directory is for thin adapters around approved third-party tools discovered through the LSM-Copilot controlled extension gate.

Adapters should:

- Expose a small Python function or CLI wrapper used by the existing analysis tools.
- Convert third-party outputs into the suite's normal CSV/JSON/figure artifacts.
- Keep measurements in physical units when voxel metadata is available.
- Avoid embedding large model weights, vendored source trees, or generated outputs.
- Include a minimal smoke-test path in the analysis summary or adjacent docs.

Before adding an adapter, verify the tool with `ai4s-web-search` and record source, license, version/commit, install command, and citation notes in `third_party/README.md` or the output summary JSON.
