import re

with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Restore zoning method selectbox and n_clusters
new_ui = """col1, col2 = st.columns(2)
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
    
with col2:
    n_clusters = st.number_input("Number of Zones (Clustering/Combined only)", min_value=2, max_value=20, value=5)
    fill_depressions = st.checkbox("Hydrologically correct DTM (Fill Depressions)", value=True)"""

content = re.sub(r'col1, col2 = st\.columns\(2\)\nwith col1:.*?fill_depressions = st\.checkbox\("Hydrologically correct DTM \(Fill Depressions\)", value=True\)', new_ui, content, flags=re.DOTALL)

with open('streamlit_app.py', 'w') as f:
    f.write(content)
