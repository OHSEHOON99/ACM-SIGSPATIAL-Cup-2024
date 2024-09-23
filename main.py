import logging
import os
import geopandas as gpd
import pandas as pd

from greedy_optimization import greedy_optimization


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


def main():
    # Set up logging
    setup_logging()

    gpkg_file = "/home/sehoon/Desktop/ACM-SIGSPATIAL-Cup-2024/data/suburban_trip_greedy.gpkg"
    tif_file = "/home/sehoon/Desktop/ACM-SIGSPATIAL-Cup-2024/data/demand_map_500.tif"
    poi_file = "/home/sehoon/Desktop/ACM-SIGSPATIAL-Cup-2024/data/Suburban_POI_Candidate.gpkg"
    output_path = "./results/"

    # Read input files
    polygons = gpd.read_file(gpkg_file)
    poi_gdf = gpd.read_file(poi_file)

    for _, polygon in polygons.iterrows(): 
        greedy_optimization(
            polygon, 
            tif_file, 
            poi_gdf, 
            capture_range=4000, 
            bandwidth=1500, 
            constraints=(1, None), 
            output_path=output_path,
            save_intermediate=True
        )

    # # Merge all GPKG files in the output path
    # merge_gpkg_files(output_path, output_file_name="suburban.gpkg")


if __name__ == "__main__":
    main()