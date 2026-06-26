# Data Policy

This repository is intended to publish the project code, documentation, configuration,
and lightweight figures for the ACM SIGSPATIAL 2024 GIS Cup EV charging station
optimization workflow.

Large raw data, processed geospatial layers, optimization outputs, and intermediate
notebook artifacts are intentionally not stored in git.

## Not Stored In Git

The following files and directories should stay local or be distributed through an
external archive:

- `data/`
- `results/`
- `outputs/`
- `post_processing/hazard_index/`
- GeoPackage, Shapefile, GeoTIFF, GraphML, CSV, Excel, and SSV outputs
- generated logs and Python cache files

## Recommended Local Layout

Use this layout when running the notebooks or scripts locally:

```text
data/
  raw/
  processed/
  road/
  poi/
  region_polygon/
  for_model/
outputs/
  results/
  logs/
```

The code and notebooks should refer to these locations with relative paths from
the repository root.

## Data Sources

The original workflow used public or competition-provided geospatial inputs,
including road networks, POI candidates, demand rasters, OD/county tables, and
hazard or outage data for Georgia, USA.

When sharing a reproducible release, place these files in an external archive
such as Zenodo, institutional storage, or a private competition data location,
then document the download URL and expected checksums here.

## Reproducibility Notes

- Keep generated optimization outputs under `outputs/` or `results/`.
- Do not commit raw geospatial data or intermediate result tables.
- If a small sample dataset is needed, add it under `examples/` with clear
  provenance and size limits.
