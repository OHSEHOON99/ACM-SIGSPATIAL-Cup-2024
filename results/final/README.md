# Curated Final Results

This directory contains selected final GeoPackage outputs from the ACM
SIGSPATIAL 2024 GIS Cup EVCS optimization workflow.

The files are kept in git because they are small enough for repository review
and represent final project outputs. Intermediate optimization traces, including
per-step accessibility arrays and supply arrays, are intentionally excluded.

## Files

- `dcfc_evcs.gpkg`: final DC fast charging station layer
- `level2_evcs.gpkg`: final Level 2 charging station layer
- `highway_dcfc.gpkg`: final highway DC fast charging station layer
- `suburban_dcfc.gpkg`: suburban DC fast charging selected sites
- `suburban_dcfc_mclp_selected.gpkg`: suburban DC fast charging MCLP-selected sites
- `suburban_lv2.gpkg`: suburban Level 2 selected sites
- `suburban_lv2_mclp_selected.gpkg`: suburban Level 2 MCLP-selected sites

These layers are derived project outputs. Raw input datasets and large
intermediate files are not stored in this repository; see `../../DATA_POLICY.md`.
