import re

with open('backend/app/api/routes.py', 'r') as f:
    content = f.read()

# Make sure to project to EPSG:4326 for GeoJSON web mapping
replacement = """    gdf = zones_to_geodataframe(zone_path)
    # Project to EPSG:4326 for standard web mapping (Folium)
    gdf = gdf.to_crs("EPSG:4326")
    geojson_path = str(Path(job_dir) / "zones.geojson")
    gdf.to_file(geojson_path, driver="GeoJSON")"""

content = re.sub(r'    gdf = zones_to_geodataframe\(zone_path\)\n    geojson_path = str\(Path\(job_dir\) / "zones\.geojson"\)\n    gdf\.to_file\(geojson_path, driver="GeoJSON"\)', replacement, content)

with open('backend/app/api/routes.py', 'w') as f:
    f.write(content)
