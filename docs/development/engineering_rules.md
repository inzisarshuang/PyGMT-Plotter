# Engineering Rules

This document explains the repository architecture behind the short rules in `AGENTS.md`.

## Ownership Boundaries

- `lib/plot_config.py`: strict cfg parsing, path resolution, scalar/list parsing, and reusable validation.
- `lib/pygmt_plotter.py`: grid conversion, profile extraction, and chainable PyGMT drawing primitives.
- `lib/geodata_preprocess.py`: geospatial raster arithmetic that is independent of figure layout.
- `plot_*/`: workflow-specific cfg loading and orchestration.
- `tests/`: fast regression checks using temporary data.

Do not copy conversion branches or configuration parsers into an entry script. Extend the owning shared module when two workflows need the same behavior.

## Configuration Compatibility

Configuration files are the public workflow interface. New options should have conservative defaults. Renaming a key requires retaining the old key as an alias for at least one release and documenting precedence when both are present.

Paths are resolved relative to the cfg location. Bare output filenames are placed under `output_dir`; explicit relative paths remain relative to the cfg location.

## Data And Memory

Raster calculations must preserve CRS and pixel alignment. Windowed reads bound peak memory by raster block size instead of scene size. Text point clouds are processed in chunks and handed to GMT as files whenever possible.

`mask_any = true` means either missing operand produces nodata. `mask_any = false` means a single missing operand contributes zero and only two missing operands produce nodata.

Intermediate files use unique names. Final products are replaced atomically so a failed process does not make a partial file appear valid.

## Plot Reproducibility

Map region, projection, scale factor, CPT, color limits, transparency, labels, and symbol styles must be visible in cfg files. Display limits affect color mapping only and never mutate input grids.

Generated images are integration-test artifacts. Inspect at least one map and one profile after changing shared plotting methods, fonts, projections, or legend placement.
