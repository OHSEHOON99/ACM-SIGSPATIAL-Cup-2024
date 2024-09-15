import numpy as np
import rasterio
from rasterio.mask import mask
from scipy.spatial.distance import cdist
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union


def process_polygon(polygon, tif_file, poi_gdf, capture_range):
    """
    Main function to process a polygon, calculate demand values, and generate distance metrics.
    """
    
    # Handle MultiPolygon: merge into a single polygon if necessary
    if isinstance(polygon.geometry, MultiPolygon):
        polygon_geom = unary_union(polygon.geometry)
    else:
        polygon_geom = polygon.geometry

    # Extract relevant polygon attributes
    polygon_id = polygon['NAMELSAD20']  # Polygon ID (e.g., name of the area)
    total_supply = polygon['total_supply']  # Total supply (e.g., EV charging ports)
    max_sites = polygon['p']  # Maximum number of POI candidates to select
    initial_selected_sites = polygon['osm_id_list']  # List of initial OSM IDs

    # 1. Calculate demand values and coordinates (apply capture_range buffer)
    buffered_polygon = polygon_geom.buffer(capture_range)
    
    with rasterio.open(tif_file) as src:
        # Mask the demand map with the buffered polygon and crop the result
        out_image, out_transform = mask(src, [buffered_polygon], crop=True)
        out_image = out_image[0]
        
        rows, cols = np.where(out_image > 0)
        demand_values = out_image[rows, cols]
        
        # Transform row/col coordinates to geographic coordinates
        demand_coords = [
            (out_transform * (col, row)) for row, col in zip(rows, cols)
        ]

    # 2. Filter POI data (only include POIs within the polygon area)
    candidate_sites_within_polygon = poi_gdf[poi_gdf.within(polygon_geom)]

    # 3. Calculate the distance matrix between demand points and POI locations
    demand_array = np.array(demand_coords)

    # Extract POI coordinates and corresponding OSM IDs
    candidate_sites_array = np.array([[point.x, point.y] for point in candidate_sites_within_polygon.geometry])
    candidate_sites_osm_ids = candidate_sites_within_polygon['osm_id'].tolist()

    # Compute the distance matrix between demand points and POI locations
    distance_matrix = cdist(demand_array, candidate_sites_array)

    return polygon_id, total_supply, max_sites, demand_values, distance_matrix, candidate_sites_osm_ids, initial_selected_sites