

# ACM-SIGSPATIAL-Cup-2024
SCSI Lab, Yonsei University

This project performs a greedy optimization algorithm for selecting sites that maximize demand coverage within a given capture range. It uses GeoTIFF files for demand mapping, polygon data for the regions, and POI (Points of Interest) data for site selection.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Running the Optimization](#running-the-optimization)
  - [Key Parameters](#key-parameters)
- [File Structure](#file-structure)
- [Examples](#examples)
- [License](#license)

## Overview
This project provides a Python implementation of a greedy optimization algorithm designed to select POI sites that optimize demand coverage within predefined polygons. The algorithm also allows for constraints on supply distribution and uses Gaussian decay functions to simulate demand decay over distances.

The key inputs to the optimization process include:

- Polygon data in GeoPackage (.gpkg) format
- Demand map in GeoTIFF (.tif) format
- Points of Interest (POI) data in GeoPackage (.gpkg) format

## Features
- **Polygon Processing**: Handles individual or multiple polygons, buffering regions to compute demand coverage.
- **Greedy Optimization**: Iteratively selects POI sites to optimize the demand coverage within a specified capture range.
- **Gaussian Decay**: Uses a Gaussian decay function to simulate decreasing demand with distance.
- **Parallel Processing**: Optimization computations are parallelized for faster execution.
- **Results Export**: Exports results in both CSV and GeoPackage formats for further analysis.

## Installation
Clone the repository:

```bash
git clone https://github.com/yourusername/polygon-greedy-optimizer.git
cd polygon-greedy-optimizer
