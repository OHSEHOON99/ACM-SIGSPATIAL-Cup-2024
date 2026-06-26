# Data Policy

This repository is intended to publish the project code, documentation, configuration,
and lightweight figures for the ACM SIGSPATIAL 2024 GIS Cup EV charging station
optimization workflow.

Large raw data, processed geospatial layers, intermediate optimization outputs,
and notebook artifacts are not bundled directly in this repository. A curated
set of final GeoPackage outputs is available under `results/final/`.

## External Files

The following files and directories should stay local or be distributed through an
external archive:

- `data/`
- `results/`, except curated final outputs under `results/final/`
- `outputs/`
- `post_processing/hazard_index/`
- intermediate GeoPackage, Shapefile, GeoTIFF, GraphML, CSV, Excel, and SSV outputs
- generated logs and Python cache files

## Included Results

The repository keeps selected final EVCS result layers under `results/final/`.
These files document the final project outputs without including the full
optimization trace.

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

- Generated optimization outputs can be written under `outputs/` or local
  `results/` paths.
- Raw geospatial data and intermediate result tables should be distributed
  through an external archive when needed for reproduction.
- Curated final outputs are kept under `results/final/`.
- If a small sample dataset is needed, add it under `examples/` with clear
  provenance and size limits.
