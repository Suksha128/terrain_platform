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
