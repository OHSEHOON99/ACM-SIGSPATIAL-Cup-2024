import logging
import os
import geopandas as gpd
import pandas as pd


def merge_gpkg_files(output_path, output_file_name):
    """
    Merge all GPKG files in the subdirectories under the output path into a single GPKG file.
    """
    gdf_list = []

    # Traverse the output_path for GPKG files
    for root, _, files in os.walk(output_path):
        for file in files:
            if file.endswith(".gpkg"):
                gpkg_file_path = os.path.join(root, file)
                try:
                    gdf = gpd.read_file(gpkg_file_path)
                    gdf_list.append(gdf)
                except Exception as e:
                    logging.error(f"Error reading {gpkg_file_path}: {str(e)}")

    # Merge all GeoDataFrames
    merged_gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))
    merged_gpkg_path = os.path.join(output_path, output_file_name)

    # Save merged GeoDataFrame as a GPKG file
    merged_gdf.to_file(merged_gpkg_path, driver="GPKG")
    logging.info(f"All GPKG files successfully merged into {merged_gpkg_path}")


def setup_logging(log_file="optimization.log"):
    """
    Configure the logging settings.
    """
    logging.basicConfig(
        level=logging.INFO,  # Set log level to INFO
        format='%(asctime)s - %(levelname)s - %(message)s',  # Set log format
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )