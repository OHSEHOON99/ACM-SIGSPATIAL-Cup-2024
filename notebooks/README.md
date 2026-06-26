# Notebooks

These notebooks are supplementary research notes from the ACM SIGSPATIAL 2024
GIS Cup EVCS workflow. They are retained to document the original exploration
and scenario runs, but the reusable implementation lives in `src/`.

Execution outputs have been stripped to keep the repository lightweight and to
avoid publishing local machine paths or traceback noise.

Run notebooks from the repository root so relative paths such as `data/...` and
`outputs/...` resolve consistently.

## Contents

- `data_preprocessing/`: demand, OD, and supply preprocessing notes
- `scenarios/`: scenario-level EVCS optimization notes
- `post_processing/`: outage, operating-hours, and hazard-risk post-processing
  notes

The large input and output files referenced by these notebooks are not stored in
git. See `../DATA_POLICY.md` for the expected local data layout.
