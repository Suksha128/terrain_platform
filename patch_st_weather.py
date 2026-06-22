import re

with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Try to find a zone to get rainfall total
summary_patch = """    summary = data.get("summary", {})
    st.subheader("Field Summary")
    scol1, scol2, scol3, scol4 = st.columns(4)
    scol1.metric("Total Zones", summary.get("total_zones", 0))
    scol2.metric("Field Status", summary.get("field_status", "N/A").split("—")[0])
    
    # Extract rainfall from first zone if available
    zones_list = data.get("zones", [])
    rain = zones_list[0].get("rainfall_total", 0.0) if zones_list else 0.0
    scol3.metric("Expected Rain (3 days)", f"{rain:.1f} mm")
    
    scol4.write(f"**Top Action:** {summary.get('top_priority_action', 'N/A')}")"""

content = re.sub(r'    summary = data\.get\("summary", \{\}\)\n    st\.subheader\("Field Summary"\)\n    scol1, scol2, scol3 = st\.columns\(3\)\n    scol1\.metric\("Total Zones", summary\.get\("total_zones", 0\)\)\n    scol2\.metric\("Field Status", summary\.get\("field_status", "N/A"\)\.split\("—"\)\[0\]\)\n    scol3\.write\(f"\*\*Top Action:\*\* \{summary\.get\(\'top_priority_action\', \'N/A\'\)\}"\)', summary_patch, content)

with open('streamlit_app.py', 'w') as f:
    f.write(content)
