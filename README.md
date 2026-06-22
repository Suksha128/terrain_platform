# 🏔️ Terrain Intelligence Platform

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-100450?style=for-the-badge&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![WhiteboxTools](https://img.shields.io/badge/WhiteboxTools-Geospatial-success?style=for-the-badge)
![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Predictive%20AI-orange?style=for-the-badge)

The **Terrain Intelligence Platform** is an enterprise-grade, geospatial analytics engine designed for precision agriculture. It leverages advanced topological physics, live weather forecasting, and machine learning to analyze Digital Terrain Models (DTMs) and automatically delineate agricultural fields into highly precise, risk-assessed management zones.

By dynamically predicting waterlogging risks before they destroy crops, this platform enables farmers and agronomists to install targeted sub-surface drainage, adjust irrigation, and significantly optimize crop yields.

---

## ✨ Core Capabilities & Advanced Accuracy

This platform doesn't just look at elevation—it physically simulates how water interacts with the landscape using state-of-the-art algorithms:

* **🌊 D-Infinity (D-Inf) Flow Tracing:** Upgraded from standard D8 algorithms, the engine utilizes D-Infinity Specific Catchment Area (SCA) algorithms to fractionally disperse water across exact angular contours. This mathematically guarantees the highest level of physical accuracy when calculating Topographic Wetness Indexes (TWI).
* **🌦️ Live Weather Integration (Open-Meteo):** The platform physically reads the GPS boundaries of uploaded GeoTIFFs, queries the Open-Meteo REST API, and dynamically injects the upcoming 3-Day rainfall forecasts directly into the Machine Learning risk assessment engine.
* **🛰️ Multi-Layer Ground Truth (NDVI & Soil Moisture):** Cross-references physical topography with satellite vegetation indexes. If the physics engine detects a deep sinkhole with a high Wetness Index, and the NDVI confirms the vegetation is dead, the algorithm mathematically escalates the risk to *Critical*.
* **🎯 Precision "Combined" Zoning:** Fuses Hydrologic Watershed generation (WhiteboxTools) with K-Means Statistical Clustering (Scikit-Learn). It first physically maps where water drains, and then mathematically clusters micro-zones within those basins to guarantee targeted drainage recommendations.
* **🗺️ Interactive Folium Mapping:** Renders zones on a live, interactive web map (via Streamlit & Folium) with EPSG:4326 reprojection and dynamic color-coded risk heatmaps.

---

## 🌍 QGIS Data Preparation Guide

To achieve the highest accuracy, your input `.tif` files must be properly formatted before uploading them to the platform. Follow these steps in QGIS:

### 1. Coordinate Reference System (CRS)
Ensure all your raster layers are projected in a **Metric CRS** (like UTM) rather than Geographic (Lat/Lon). 
- Right-click your layer -> `Export` -> `Save As`.
- Set the CRS to your local UTM zone (e.g., `EPSG:32644`).
- This ensures elevation and flow accumulation are calculated in square meters, not degrees!

### 2. Digital Terrain Model (`dtm.tif`)
- Ensure the DTM is a **Single Band** Float32 raster.
- NoData values should be properly set (e.g., `-9999`) to prevent the physics engine from routing water off the edge of the map.
- Export as `dtm.tif`.

### 3. Generating NDVI (`ndvi.tif`)
If you are using Multispectral satellite imagery (like Sentinel-2 or Landsat), you must calculate the NDVI before uploading:
1. Open the **Raster Calculator** in QGIS (`Raster` -> `Raster Calculator`).
2. Identify your Red and Near-Infrared (NIR) bands. *(For Sentinel-2: Band 4 is Red, Band 8 is NIR).*
3. Enter the NDVI formula:
   ```text
   ( "Band_NIR" - "Band_Red" ) / ( "Band_NIR" + "Band_Red" )
   ```
4. Export the resulting single-band output as `ndvi.tif`.

### 4. File Naming Convention
The platform automatically maps your data based on the filename. Please name your exported GeoTIFFs exactly as follows:
- `dtm.tif` (Required)
- `ndvi.tif` (Optional - highly recommended for crop health ground truth)
- `slope.tif` (Optional - platform will auto-generate if missing)
- `soil_moisture.tif` (Optional)

---

## 🏗️ System Architecture

The platform is split into a highly decoupled Backend engine and a lightweight Frontend dashboard.

### 1. The Engine (FastAPI Backend)
Located in the `/backend` directory.
- **RESTful API:** Powered by FastAPI for lightning-fast async processing.
- **Geospatial Processing:** Powered by `rasterio`, `geopandas`, and `WhiteboxTools` for heavy raster math.
- **Machine Learning:** Scikit-Learn `RandomForestClassifier` backed by a robust heuristic rule-based fallback engine.

### 2. The Dashboard (Streamlit Frontend)
Located at the root (`streamlit_app.py`).
- **State Management:** Secure `st.session_state` handling allows users to interact with maps without dropping the API connection.
- **Visual Analytics:** Interactive GeoJSON rendering via `streamlit-folium`.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- WhiteboxTools executable installed and accessible.

### 1. Start the Backend Engine
The backend performs all the heavy lifting and ML inference.
```bash
cd backend
python3 -m uvicorn app.main:app --port 8000 --reload
```

### 2. Start the Frontend Dashboard
Open a new terminal window and launch the Streamlit app.
```bash
python3 -m streamlit run streamlit_app.py
```

### 3. Run an Analysis
1. Navigate to `http://localhost:8501` in your browser.
2. Upload your raw `.tif` files (e.g., `dtm.tif`, `slope.tif`, `ndvi.tif`). The system will auto-map them based on filenames.
3. Select the **Combined** zoning method for maximum accuracy.
4. Click **Run Analysis** and explore the interactive Risk Map!

---

## 🛠️ Built With

* **WhiteboxTools:** Core hydrological physics engine.
* **FastAPI:** High-performance asynchronous backend framework.
* **Streamlit:** Interactive Python-driven frontend.
* **Scikit-Learn:** Machine learning and K-Means clustering.
* **Rasterio & GeoPandas:** Geospatial vector and raster manipulations.
* **Folium:** Leaflet.js interactive maps.
* **Open-Meteo:** Live meteorological forecasting API.

---
*Developed for advanced agricultural intelligence and terrain optimization.*
