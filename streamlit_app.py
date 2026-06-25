import streamlit as st
import requests
import pandas as pd
import json
import folium
from streamlit_folium import st_folium
import geopandas as gpd

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Terrain Intelligence Platform", page_icon="🏔️", layout="wide")

st.title("🏔️ Terrain Intelligence Platform")
st.markdown("Analyze agricultural field DEMs (GeoTIFFs) to derive terrain features, delineate management zones, and predict waterlogging risk.")

if "job_id" not in st.session_state:
    st.session_state.job_id = None
    st.session_state.analysis_data = None

st.header("1. Upload Terrain Files")
st.markdown("Upload multiple GeoTIFF files. The system will auto-map based on filenames (e.g., `dtm.tif`, `dem.tif`, `ndvi.tif`).")

uploaded_files = st.file_uploader("Upload .tif/.tiff files", type=["tif", "tiff"], accept_multiple_files=True)

if uploaded_files and st.button("Upload Files"):
    with st.spinner("Uploading and mapping files..."):
        files = [("files", (f.name, f.read(), "image/tiff")) for f in uploaded_files]
        
        try:
            res = requests.post(f"{API_BASE}/upload_folder", files=files)
            if res.status_code == 200:
                data = res.json()
                st.session_state.job_id = data["job_id"]
                st.success(f"Upload successful! Job ID: {data['job_id']}")
                st.info(f"Mapped features: {', '.join(data.get('mapped_features', []))}")
            else:
                st.error(f"Upload failed: {res.text}")
        except Exception as e:
            st.error(f"Connection error: {e}")

st.header("2. Configuration")

col1, col2 = st.columns(2)
with col1:
    zone_method = st.selectbox(
        "Zoning Method",
        options=["hydrologic", "combined", "terrain_cluster"],
        format_func=lambda x: {
            "hydrologic": "Hydrologic (Trace water - most accurate for large maps)",
            "combined": "Combined (Precision targeting within basins)",
            "terrain_cluster": "Clustering (Forced statistical multi-zones for small crops)"
        }.get(x, x)
    )
    model_type = "random_forest"
    soil_type = st.selectbox(
        "Primary Soil Type",
        options=["Loam (Standard)", "Clay (High Runoff)", "Sand (High Infiltration)"],
        index=0
    )
    
with col2:
    n_clusters = st.number_input("Number of Zones (Clustering/Combined only)", min_value=2, max_value=20, value=5)
    fill_depressions = st.checkbox("Hydrologically correct DTM (Fill Depressions)", value=True)

if st.button("Run Analysis", disabled=not st.session_state.job_id, type="primary"):
    with st.spinner("Analyzing terrain and running ML predictions... This may take a moment."):
        payload = {
            "job_id": st.session_state.job_id,
            "zone_method": zone_method,
            "n_clusters": n_clusters,
            "fill_depressions": fill_depressions,
            "model_type": model_type,
            "target_crs": "EPSG:32644",
            "soil_type": soil_type.split()[0] # Sends "Loam", "Clay", or "Sand"
        }
        
        try:
            res = requests.post(f"{API_BASE}/analyze", json=payload)
            if res.status_code == 200:
                st.session_state.analysis_data = res.json()
                st.success("Analysis Complete!")
            else:
                st.error(f"Analysis failed: {res.text}")
        except Exception as e:
            st.error(f"Connection error: {e}")

if st.session_state.analysis_data:
    data = st.session_state.analysis_data
    st.header("Analysis Results")

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
                
            features = geojson_data.get("features", [])
            if features:
                for f in features:
                    zid = str(f["properties"].get("zone_id", ""))
                    f["properties"]["zone_id"] = zid
                    f["properties"]["Risk_Level"] = "Unknown"
                    
                    if "Center_Lat" not in f["properties"] or f["properties"]["Center_Lat"] is None:
                        f["properties"]["Center_Lat"] = "Click 'Run Analysis' again"
                    if "Center_Lon" not in f["properties"] or f["properties"]["Center_Lon"] is None:
                        f["properties"]["Center_Lon"] = "Click 'Run Analysis' again"
                        
                    for p in data.get("predictions", []):
                        if str(p.get("zone_id", "")) == zid:
                            f["properties"]["Risk_Level"] = p.get("waterlogging_risk", "Unknown")
                            break
                            
                try:
                    coords = features[0]["geometry"]["coordinates"][0][0]
                    if isinstance(coords[0], list): coords = coords[0]
                    m = folium.Map(location=[coords[1], coords[0]], zoom_start=14)
                    
                    folium.GeoJson(
                        geojson_data,
                        style_function=style_fn,
                        tooltip=folium.GeoJsonTooltip(
                            fields=["zone_id", "Risk_Level", "Center_Lat", "Center_Lon"], 
                            aliases=["Zone ID:", "Risk Level:", "Latitude:", "Longitude:"]
                        )
                    ).add_to(m)
                    
                    st.subheader("Interactive Risk Map")
                    st_folium(m, width=1200, height=500)
                except Exception as e:
                    st.warning(f"Could not center map: {e}")
    except Exception as e:
        st.warning(f"Could not load map: {e}")

    summary = data.get("summary", {})
    st.subheader("Field Summary")
    scol1, scol2, scol3, scol4 = st.columns(4)
    scol1.metric("Total Zones", summary.get("total_zones", 0))
    scol2.metric("Field Status", summary.get("field_status", "N/A").split("—")[0])
    
    # Extract rainfall from first zone if available
    zones_list = data.get("zones", [])
    rain = zones_list[0].get("rainfall_total", 0.0) if zones_list else 0.0
    scol3.metric("Expected Rain (3 days)", f"{rain:.1f} mm")
    
    scol4.write(f"**Top Action:** {summary.get('top_priority_action', 'N/A')}")
    
    st.subheader("Zone Details")
    for pred in data.get("predictions", []):
        zone_stats = next((z for z in data.get("zones", []) if z["zone_id"] == pred["zone_id"]), None)
        
        # Extract coordinates for UI text display in case map tooltips cache
        lat, lon = "N/A", "N/A"
        if "geojson_data" in locals():
            for f in geojson_data.get("features", []):
                if f["properties"].get("zone_id") == pred["zone_id"]:
                    lat = f["properties"].get("Center_Lat", "N/A")
                    lon = f["properties"].get("Center_Lon", "N/A")
                    break

        with st.expander(f"Zone {pred['zone_id']} - {pred['waterlogging_risk']} Risk (Lat: {lat}, Lon: {lon})"):
            if zone_stats:
                cols = st.columns(5)
                cols[0].metric("Elevation (m)", f"{zone_stats['mean_elevation']:.1f}")
                cols[1].metric("Slope (deg)", f"{zone_stats['mean_slope']:.1f}")
                cols[2].metric("TWI", f"{zone_stats['mean_twi']:.2f}")
                cols[3].metric("Depression (m)", f"{zone_stats['mean_depression_depth']:.2f}")
                chm_val = f"{zone_stats['mean_chm']:.2f}" if zone_stats.get('mean_chm') is not None else "N/A"
                cols[4].metric("Canopy (m)", chm_val)
                
            st.write(f"**Drainage Priority:** {pred['drainage_priority']}")
            st.write(f"**Irrigation:** {pred['irrigation_recommendation']}")
            st.write("**Key Drivers:**")
            for d in pred['key_drivers']:
                st.write(f"- {d}")

    st.markdown("---")
    st.subheader("📥 Export Insights")
    colA, colB = st.columns(2)
    
    with colA:
        json_str = json.dumps(data, indent=2)
        st.download_button(
            label="📄 Download Full Report (JSON)",
            file_name=f"terrain_insights_{st.session_state.job_id}.json",
            mime="application/json",
            data=json_str,
            use_container_width=True
        )
        
    with colB:
        zones_list = data.get("zones", [])
        preds_list = data.get("predictions", [])
        if zones_list and preds_list:
            df_zones = pd.DataFrame(zones_list)
            df_preds = pd.DataFrame(preds_list)
            df_merged = pd.merge(df_zones, df_preds, on="zone_id", how="left")
            
            # Convert list columns to strings to prevent CSV issues
            if "key_drivers" in df_merged.columns:
                df_merged["key_drivers"] = df_merged["key_drivers"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
                
            csv_data = df_merged.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📊 Download Zone Data (CSV)",
                file_name=f"zone_data_{st.session_state.job_id}.csv",
                mime="text/csv",
                data=csv_data,
                use_container_width=True
            )

