import logging
import os
import geopandas as gpd
import pandas as pd

import geopandas as gpd
import matplotlib.pyplot as plt
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

def process_ev_charging_data(initial_pois_path, candidate_pois_path, polygons_path, charger_type, urban_polygons_path, region_type, save=True):
    """
    Processes and visualizes the EV charging data for a given region based on the selected charger type (lv2 or dcfc) and region type.
    """
    
    # Step 1: Load the data
    initial_pois_gdf = gpd.read_file(initial_pois_path)
    candidate_pois_gdf = gpd.read_file(candidate_pois_path)
    polygons_gdf = gpd.read_file(polygons_path)
    urban_polygons_gdf = gpd.read_file(urban_polygons_path)

    # Step 2: Ensure all GeoDataFrames use the same coordinate system (EPSG:3857)
    crs_epsg = 3857
    initial_pois_gdf, candidate_pois_gdf, polygons_gdf, urban_polygons_gdf = \
        [gdf.to_crs(epsg=crs_epsg) for gdf in [initial_pois_gdf, candidate_pois_gdf, polygons_gdf, urban_polygons_gdf]]
    
    # Step 3: Validate charger_type and select the appropriate column
    charger_column = 'lv2_count' if charger_type == 'lv2' else 'dcfc_count'
    polygons_gdf = polygons_gdf[['NAMELSAD20', charger_column, 'geometry']].rename(columns={charger_column: 'total_supply'})

    # Ensure that total_supply is present in initial_pois_gdf, if not, create it from the appropriate charger count
    if 'total_supply' not in initial_pois_gdf.columns:
        if charger_type == 'lv2' and 'lv2_count' in initial_pois_gdf.columns:
            initial_pois_gdf['total_supply'] = initial_pois_gdf['lv2_count']
        elif charger_type == 'dcfc' and 'dcfc_count' in initial_pois_gdf.columns:
            initial_pois_gdf['total_supply'] = initial_pois_gdf['dcfc_count']
        else:
            raise KeyError("Neither 'lv2_count' nor 'dcfc_count' is available to create 'total_supply'.")
    
    # Print basic statistics
    print(f"Initial POIs within {region_type} polygons: {initial_pois_gdf.shape[0]}")
    print(f"Candidate POIs within {region_type} polygons: {candidate_pois_gdf.shape[0]}")

    # Step 4: Calculate POI counts and osm_id lists for polygons
    polygons_gdf = calculate_poi_counts_and_osm_ids(polygons_gdf, initial_pois_gdf, 'initial_count')

    # Step 5: Repeat POI counting for candidate POIs without osm_id_list
    polygons_gdf = calculate_poi_counts(polygons_gdf, candidate_pois_gdf, 'candidate_count')

    # Step 6: Calculate p values based on candidate count and total supply
    polygons_gdf['p'] = polygons_gdf.apply(calculate_p, threshold=4, axis=1)

    # Adjust p values based on the candidate count
    polygons_gdf['p'] = polygons_gdf.apply(lambda row: min(row['p'], row['candidate_count']), axis=1)

    # Step 7: Separate polygons into MCLP and Greedy categories based on p
    mclp_polygons = polygons_gdf[polygons_gdf['p'] == 1]
    greedy_polygons = polygons_gdf[polygons_gdf['p'] > 1]

    # Use initial POIs for MCLP polygons and perform spatial join
    points_in_mclp_polygons = gpd.GeoDataFrame()
    if not mclp_polygons.empty:
        points_in_mclp_polygons = initial_pois_gdf[initial_pois_gdf.intersects(mclp_polygons.unary_union)][['osm_id', 'geometry', 'total_supply']]

    # Step 8: Save results if requested
    if save:
        save_gpkg(greedy_polygons, f'{region_type}_{charger_type}_greedy.gpkg')
        if not points_in_mclp_polygons.empty:
            save_gpkg(points_in_mclp_polygons, f'{region_type}_{charger_type}_mclp_selected.gpkg')

    # Step 9: Visualize results with subplots
    visualize_ev_charging_data_with_subplots(urban_polygons_gdf, initial_pois_gdf, candidate_pois_gdf, greedy_polygons, charger_type)


def calculate_poi_counts_and_osm_ids(polygons_gdf, pois_gdf, count_column):
    """
    Calculates the number of POIs within each polygon and stores the count in a new column.
    Additionally, creates a list of osm_ids for each polygon where applicable.
    """
    # Perform spatial join
    pois_within_polygons = gpd.sjoin(pois_gdf[['osm_id', 'geometry']], polygons_gdf, how='left', predicate='within')

    # Aggregate osm_id lists and calculate counts
    if pois_within_polygons.shape[0] > 0:
        # Calculate POI counts for each polygon and store in count_column
        polygons_gdf[count_column] = pois_within_polygons.groupby('index_right').size()

        # Create osm_id_list for each polygon, converting osm_id to string
        polygons_gdf['osm_id_list'] = pois_within_polygons.groupby('index_right')['osm_id'].agg(lambda x: [str(osm_id) for osm_id in x])

        # Convert empty lists to NaN or filter them out
        polygons_gdf['osm_id_list'] = polygons_gdf['osm_id_list'].apply(lambda x: x if x and len(x) > 0 else None)
    else:
        print("Warning: No matching points were found within polygons.")
        polygons_gdf[count_column] = 0
        polygons_gdf['osm_id_list'] = None

    return polygons_gdf


def calculate_p(row, threshold):
    """
    Calculates the p value based on candidate count and total supply.
    """
    if row['candidate_count'] == 1 or row['total_supply'] <= threshold:
        return 1
    return max(row['total_supply'] // threshold, 2)


def save_gpkg(gdf, path):
    """
    Saves a GeoDataFrame to a GeoPackage file.
    """
    gdf.to_file(path, driver='GPKG')
    print(f"Data saved to {path}")


def visualize_ev_charging_data_with_subplots(urban_polygons_gdf, initial_pois_gdf, candidate_pois_gdf, greedy_polygons_gdf, charger_type):
    """
    Visualizes urban polygons and POI data using two subplots. 
    One subplot shows the polygons and candidate/initial POIs, 
    and the other shows the polygons colored by p_value.
    """
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))

    # Subplot 1: Plot urban polygons and POIs (initial and candidate)
    urban_polygons_gdf.plot(ax=axes[0], color='lightgray', edgecolor='black', alpha=0.5, label='Urban Polygon')
    candidate_pois_gdf.plot(ax=axes[0], marker='x', color='red', markersize=50, label='Candidate POI', alpha=0.7)
    initial_pois_gdf.plot(ax=axes[0], marker='o', color='blue', markersize=20, label='Initial POI', alpha=0.7)
    axes[0].set_title(f'Polygons and POIs (Initial and Candidate) - {charger_type.upper()}', fontsize=15)
    axes[0].set_xlabel('Longitude', fontsize=12)
    axes[0].set_ylabel('Latitude', fontsize=12)
    axes[0].legend()

    # Subplot 2: Plot polygons colored by p_value
    colormap = plt.get_cmap('OrRd')
    norm = plt.Normalize(vmin=greedy_polygons_gdf['p'].min(), vmax=greedy_polygons_gdf['p'].max())
    greedy_polygons_gdf.plot(column='p', cmap=colormap, linewidth=0.8, edgecolor='black', norm=norm, legend=True, ax=axes[1])
    axes[1].set_title(f'Polygons by p Values ({charger_type.upper()} Charging)', fontsize=15)
    axes[1].set_xlabel('Longitude', fontsize=12)
    axes[1].set_ylabel('Latitude', fontsize=12)

    plt.tight_layout()
    plt.show()


def calculate_poi_counts(polygons_gdf, pois_gdf, count_column):
    """
    Calculates the number of POIs within each polygon and stores the count in a new column.
    """
    pois_within_polygons = gpd.sjoin(polygons_gdf, pois_gdf, how='left', predicate='contains')
    polygons_gdf[count_column] = pois_within_polygons.groupby(pois_within_polygons.index).size()
    return polygons_gdf