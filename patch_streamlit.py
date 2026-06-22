import re

with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Remove zone_method selectbox
content = re.sub(
    r'zone_method = st.selectbox\([\s\S]*?\]\n    \)',
    'zone_method = "hydrologic"',
    content
)

# Remove n_clusters slider
content = re.sub(
    r'if zone_method == "terrain_cluster":[\s\S]*?else:\n        n_clusters = 5',
    'n_clusters = 5',
    content
)

# Remove model_type selectbox
content = re.sub(
    r'model_type = st\.selectbox\("Model Type", \["random_forest", "xgboost", "lightgbm"\]\)',
    'model_type = "random_forest"',
    content
)

with open('streamlit_app.py', 'w') as f:
    f.write(content)
