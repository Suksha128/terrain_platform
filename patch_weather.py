import re

with open('backend/app/api/routes.py', 'r') as f:
    content = f.read()

# Add imports for weather
if 'from pyproj import Transformer' not in content:
    content = content.replace('import json', 'import json\nimport requests as req\nimport rasterio\nfrom pyproj import Transformer')

# Add fetch_weather function
weather_func = """def fetch_weather_forecast(dtm_path: str) -> float:
    try:
        with rasterio.open(dtm_path) as src:
            bounds = src.bounds
            crs = src.crs
            center_x = (bounds.left + bounds.right) / 2
            center_y = (bounds.bottom + bounds.top) / 2
            
        transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(center_x, center_y)
        
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum&timezone=auto&forecast_days=3"
        res = req.get(url)
        if res.status_code == 200:
            data = res.json()
            sums = data.get("daily", {}).get("precipitation_sum", [])
            valid_sums = [s for s in sums if s is not None]
            return sum(valid_sums) if valid_sums else 0.0
    except Exception as e:
        print(f"Weather API failed: {e}")
    return 0.0

@router.post("/analyze", response_model=AnalysisResult)"""

if 'def fetch_weather_forecast' not in content:
    content = content.replace('@router.post("/analyze", response_model=AnalysisResult)', weather_func)

# Call fetch_weather inside analyze
if 'total_rain = fetch_weather_forecast' not in content:
    content = content.replace(
        'zones = compute_zonal_stats(zone_path, feat_paths)',
        'total_rain = fetch_weather_forecast(str(dtm_path))\n    zones = compute_zonal_stats(zone_path, feat_paths, rainfall_total=total_rain)'
    )

with open('backend/app/api/routes.py', 'w') as f:
    f.write(content)
