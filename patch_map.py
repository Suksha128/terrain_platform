import re

with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Add imports
if 'import folium' not in content:
    content = content.replace('import json', 'import json\nimport folium\nfrom streamlit_folium import st_folium\nimport geopandas as gpd')

# Add map visualization right after Analysis Results header
map_code = """st.header("Analysis Results")
                
                try:
                    geo_res = requests.get(f"{API_BASE}/zones/{st.session_state.job_id}")
                    if geo_res.status_code == 200:
                        geojson_data = geo_res.json()
                        
                        risk_colors = {}
                        for p in data.get("predictions", []):
                            if p["waterlogging_risk"] == "High":
                                risk_colors[p["zone_id"]] = "#ff4b4b"
                            elif p["waterlogging_risk"] == "Medium":
                                risk_colors[p["zone_id"]] = "#ffa000"
                            else:
                                risk_colors[p["zone_id"]] = "#00c853"
                                
                        def style_fn(feature):
                            zid = feature["properties"]["zone_id"]
                            color = risk_colors.get(zid, "#3388ff")
                            return {"fillColor": color, "color": "black", "weight": 2, "fillOpacity": 0.6}
                            
                        # Find center from bounds
                        features = geojson_data.get("features", [])
                        if features:
                            # just grab first coord of first feature for center
                            try:
                                coords = features[0]["geometry"]["coordinates"][0][0]
                                if isinstance(coords[0], list): coords = coords[0] # handle multipolygon
                                m = folium.Map(location=[coords[1], coords[0]], zoom_start=14)
                                
                                folium.GeoJson(
                                    geojson_data,
                                    style_function=style_fn,
                                    tooltip=folium.GeoJsonTooltip(fields=["zone_id"], aliases=["Zone ID: "])
                                ).add_to(m)
                                
                                st.subheader("Interactive Risk Map")
                                st_folium(m, width=1200, height=500)
                            except Exception as e:
                                st.warning(f"Could not center map: {e}")
                except Exception as e:
                    st.warning(f"Could not load map: {e}")
"""

content = re.sub(r'st\.header\("Analysis Results"\)', map_code, content)

with open('streamlit_app.py', 'w') as f:
    f.write(content)
