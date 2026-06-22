import sys
sys.path.append('backend')
from app.services.zoning import delineate_watersheds, zones_to_geodataframe
from pathlib import Path
delineate_watersheds("backend/results/5ed21a7a/flow_direction.tif", "backend/results/5ed21a7a/flow_accumulation.tif", "backend/results/5ed21a7a")
gdf = zones_to_geodataframe("backend/results/5ed21a7a/watersheds.tif")
print(f"Number of zones: {len(gdf)}")
