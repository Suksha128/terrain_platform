import re

with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Initialize state
if 'st.session_state.analysis_data = None' not in content:
    content = content.replace('st.session_state.job_id = None', 'st.session_state.job_id = None\n    st.session_state.analysis_data = None')

# Refactor the Run Analysis button logic
new_logic = """if st.button("Run Analysis", disabled=not st.session_state.job_id, type="primary"):
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
                st.session_state.analysis_data = res.json()
                st.success("Analysis Complete!")
            else:
                st.error(f"Analysis failed: {res.text}")
        except Exception as e:
            st.error(f"Connection error: {e}")

if st.session_state.analysis_data:
    data = st.session_state.analysis_data
    st.header("Analysis Results")
"""

# Replace the giant if block
content = re.sub(r'if st\.button\("Run Analysis".*?st\.header\("Analysis Results"\)', new_logic, content, flags=re.DOTALL)

with open('streamlit_app.py', 'w') as f:
    f.write(content)
