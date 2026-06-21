import streamlit as st
import requests
import pandas as pd
import json

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Terrain Intelligence Platform", page_icon="🏔️", layout="wide")

st.title("🏔️ Terrain Intelligence Platform")
st.markdown("Analyze agricultural field DEMs (GeoTIFFs) to derive terrain features, delineate management zones, and predict waterlogging risk.")

if "job_id" not in st.session_state:
    st.session_state.job_id = None

st.header("1. Upload Terrain Files")
st.markdown("Upload multiple GeoTIFF files. The system will auto-map based on filenames (e.g. `dtm.tif`, `slope.tif`, `ndvi.tif`).")

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
    st.info("Using Most Accurate Method: Hydrologic Zones & Auto-selected ML Model")
    zone_method = "hydrologic"
    model_type = "random_forest"
    
with col2:
    n_clusters = 5
    fill_depressions = st.checkbox("Hydrologically correct DTM (Fill Depressions)", value=True)

if st.button("Run Analysis", disabled=not st.session_state.job_id, type="primary"):
    with st.spinner("Analyzing terrain and running ML predictions... This may take a moment."):
        payload = {
            "job_id": st.session_state.job_id,
            "zone_method": zone_method,
            "n_clusters": n_clusters,
            "fill_depressions": fill_depressions,
            "model_type": model_type,
            "target_crs": "EPSG:32644"
        }
        
        try:
            res = requests.post(f"{API_BASE}/analyze", json=payload)
            if res.status_code == 200:
                data = res.json()
                st.success("Analysis Complete!")
                
                st.header("Analysis Results")
                
                summary = data.get("summary", {})
                st.subheader("Field Summary")
                scol1, scol2, scol3 = st.columns(3)
                scol1.metric("Total Zones", summary.get("total_zones", 0))
                scol2.metric("Field Status", summary.get("field_status", "N/A").split("—")[0])
                scol3.write(f"**Top Action:** {summary.get('top_priority_action', 'N/A')}")
                
                st.subheader("Zone Details")
                for pred in data.get("predictions", []):
                    zone_stats = next((z for z in data.get("zones", []) if z["zone_id"] == pred["zone_id"]), None)
                    
                    with st.expander(f"Zone {pred['zone_id']} - {pred['waterlogging_risk']} Risk"):
                        if zone_stats:
                            cols = st.columns(4)
                            cols[0].metric("Elevation (m)", f"{zone_stats['mean_elevation']:.1f}")
                            cols[1].metric("Slope (deg)", f"{zone_stats['mean_slope']:.1f}")
                            cols[2].metric("TWI", f"{zone_stats['mean_twi']:.2f}")
                            cols[3].metric("Depression (m)", f"{zone_stats['mean_depression_depth']:.2f}")
                            
                        st.write(f"**Drainage Priority:** {pred['drainage_priority']}")
                        st.write(f"**Irrigation:** {pred['irrigation_recommendation']}")
                        st.write("**Key Drivers:**")
                        for d in pred['key_drivers']:
                            st.write(f"- {d}")
                            
            else:
                st.error(f"Analysis failed: {res.text}")
        except Exception as e:
            st.error(f"Connection error: {e}")
