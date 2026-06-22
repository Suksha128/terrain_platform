import requests

payload = {
    "job_id": "5ed21a7a",
    "zone_method": "terrain_cluster",
    "n_clusters": 5,
    "fill_depressions": True,
    "model_type": "random_forest",
    "target_crs": "EPSG:32644"
}
print("Analyzing...")
res = requests.post("http://localhost:8000/analyze", json=payload)
print("Analyze:", res.text)
