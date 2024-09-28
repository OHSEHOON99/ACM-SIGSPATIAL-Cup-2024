import logging
import os

import geopandas as gpd
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from .capacity_optimizer import CapacityOptimizer
from .process_polygon import process_polygon


def update_supply(poi_supply, selected_sites, supply_values):
    """
    A function that updates the supply for sites selected by the greedy algorithm.

    Args:
    - poi_supply (np.ndarray): Array representing the supply for all candidate sites.
    - selected_sites (list or np.ndarray): Indices of the selected sites whose supply will be updated.
    - supply_values (float or list): Supply values to be assigned to the selected sites.

    Returns:
    - np.ndarray: Updated supply array with new values for the selected sites.
    """
    poi_supply[selected_sites] = supply_values
    return poi_supply


def log_polygon_info(polygon_id, total_supply, optimizer, selected_sites, distance_matrix, demand_values):
    """
    Log information about the processed region polygon.
    """
    line_length = max(50, len(f"Processed Polygon ID: {polygon_id}") + 4)
    log_message = (
        f"\n{'=' * line_length}\n"
        f"*** Processed Polygon Information ***\n"
        f"{'-' * line_length}\n"
        f"Polygon ID            : {polygon_id}\n"
        f"Total Supply          : {total_supply}\n"
        f"A_bar Value           : {optimizer.A_bar_value:.4f}\n"
        f"Selected Initial Sites: {len(selected_sites)}\n"
        f"Initial Coverage      : {optimizer.calculate_coverage(selected_sites, distance_matrix, demand_values):.2f}%\n"
        f"{'=' * line_length}"
    )
    logging.info(log_message)


def log_optimization_step(n, max_sites, best_site, best_A_hat, coverage_ratio):
    """
    Log optimization details for each step.
    """
    log_message = f"Selecting site {n:2}/{max_sites:2} | Selected Site: {best_site:3} | A_hat: {best_A_hat:.5f} | Coverage: {coverage_ratio:6.2f}%"
    logging.info(log_message)


def greedy_optimization(polygon, tif_file, poi_gdf, capture_range, bandwidth, constraints, output_path, save_intermediate=False):
    """
    Perform greedy optimization to select Electric Vehicle Charging Station (EVCS) locations and optimize supply distribution
    within a given region polygon.

    This function applies a greedy algorithm to iteratively select the optimal EVCS sites from a set of candidate Points of Interest (POI).
    At each step, it calculates the optimal supply distribution using Quadratic Programming (QP) to minimize the 2SFCA (Two-Step Floating 
    Catchment Area) Accessibility Index at demand points. The site that minimizes the standard deviation of the accessibility index is selected 
    in each iteration. Optionally, intermediate results can be saved, including the supply distribution and accessibility index at each step.

    Args:
    - polygon (GeoSeries): The polygon geometry representing the region of interest for optimization.
    - tif_file (str): Path to the demand GeoTIFF file.
    - poi_gdf (GeoDataFrame): GeoDataFrame containing candidate POI data, including OSM IDs and coordinates for potential EVCS locations.
    - capture_range (int): The maximum coverage radius for demand coverage calculation.
    - bandwidth (int): The bandwidth for the Gaussian decay function in optimization.
    - constraints (tuple): A tuple specifying the lower and upper limits for site selection (e.g., (min_sites, max_sites)).
    - output_path (str): Directory to save the output files (intermediate and final results).
    - save_intermediate (bool, optional): If True, saves intermediate results such as supply distribution and coverage at each step.

    Returns:
    - None: Results are saved as CSV and GPKG files in the specified output directory.
    """

    # Process the given polygon to extract relevant optimization data
    result = process_polygon(polygon, tif_file, poi_gdf, capture_range)
    polygon_id, total_supply, max_sites, demand_values, distance_matrix, candidate_sites, initial_selected_sites = result
    optimizer = CapacityOptimizer(total_supply, demand_values, distance_matrix, bandwidth=bandwidth, capture_range=capture_range)

    # Select initial sites based on the initial POIs
    selected_sites = [i for i, osm_id in enumerate(candidate_sites) if osm_id in initial_selected_sites]
    initial_site_count = len(selected_sites)

    # Log processed polygon information
    log_polygon_info(polygon_id, total_supply, optimizer, selected_sites, distance_matrix, demand_values)

    # Initialize the supply array and assign initial supply to the selected sites
    poi_supply = np.zeros(len(candidate_sites))
    initial_supply_value = total_supply / len(selected_sites)
    poi_supply[selected_sites] = initial_supply_value

    # Update the list of candidate sites (exclude already selected ones)
    remaining_candidate_sites = list(set(range(len(poi_supply))) - set(selected_sites))

    results_list = []

    # Create directories for intermediate results if needed
    if save_intermediate:
        supply_path = os.path.join(output_path, polygon_id, "supply")
        ai_path = os.path.join(output_path, polygon_id, "Ai")
        os.makedirs(supply_path, exist_ok=True)
        os.makedirs(ai_path, exist_ok=True)

    for n in range(initial_site_count + 1, max_sites + 1):
        best_site = None
        best_A_hat = np.inf
        best_optimized_supply = None
        best_Ai_optimized = None

        # Parallel optimization for candidate site selection
        results = Parallel(n_jobs=os.cpu_count())(
            delayed(lambda site: (optimizer.optimize_capacity(selected_sites + [site], demand_values, constraints), site))(site)
            for site in remaining_candidate_sites
        )

        all_infinite = True

        for ((optimized_supply, Ai_optimized, A_hat), site) in results:
            if A_hat < best_A_hat:
                best_A_hat = A_hat
                best_site = site
                best_optimized_supply = optimized_supply
                best_Ai_optimized = Ai_optimized
                all_infinite = False

        if all_infinite:
            logging.warning(f"All A_hat values are infinite at step {n}. There's no any solutions for the optimal supply. Terminating early.")
            break

        # Calculate coverage after optimization
        coverage_ratio = optimizer.calculate_coverage(selected_sites, distance_matrix, demand_values)

        # Log the optimization result for this step
        log_optimization_step(n, max_sites, best_site, best_A_hat, coverage_ratio)

        # Calculate additional optimization metrics
        min_Ai, max_Ai, MD, MAD, CV, Gini = optimizer.calculate_metrics(best_Ai_optimized, demand_values)[1:]

        # Update selected sites and remove the chosen site from the candidate list
        selected_sites.append(best_site)
        remaining_candidate_sites.remove(best_site)

        # Update the supply for the selected sites
        poi_supply = update_supply(poi_supply, selected_sites, best_optimized_supply)

        # Store the optimization result for this step
        result = {
            'Step': n,
            'Selected_Site': best_site,
            'A_hat': best_A_hat,
            'min_Ai': min_Ai,
            'max_Ai': max_Ai,
            'MD': MD,
            'MAD': MAD,
            'CV': CV,
            'Gini': Gini
        }

        results_list.append(result)

        # Save intermediate results if required
        if save_intermediate:
            np.savetxt(os.path.join(supply_path, f"supply_{n}.ssv"), poi_supply, delimiter=' ', fmt='%.4f')
            np.savetxt(os.path.join(ai_path, f"Ai_{n}.ssv"), best_Ai_optimized, delimiter=" ")

    # Create the output directory for the polygon-specific results
    polygon_output_path = os.path.join(output_path, str(polygon_id))
    os.makedirs(polygon_output_path, exist_ok=True)

    # Save the final results as a CSV file
    pd.DataFrame(results_list).to_csv(os.path.join(output_path, polygon_id, f"{polygon_id}.csv"), index=False)

    # Create a DataFrame of selected POIs and their corresponding supply
    selected_poi_df = pd.DataFrame({
        'osm_id': [candidate_sites[i] for i in selected_sites],
        'supply': [poi_supply[i] for i in selected_sites]
    })

    # Merge the selected POI data with the original POI DataFrame to include 'fclass' and 'geometry'
    gdf_selected_poi = pd.merge(
        selected_poi_df,
        poi_gdf[['osm_id', 'fclass', 'geometry']],
        on='osm_id',
        how='left'
    )

    # Reorder columns and save the result as a GeoPackage (GPKG) file
    gpd.GeoDataFrame(gdf_selected_poi[['osm_id', 'fclass', 'supply', 'geometry']], geometry='geometry')\
        .set_crs(epsg=3857)\
        .to_file(os.path.join(output_path, polygon_id, f"{polygon_id}.gpkg"), layer=polygon_id, driver="GPKG")

    # Log the completion of the optimization process
    logging.info(f"Optimization process for {polygon_id} complete")
