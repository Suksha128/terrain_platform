import re

with open('streamlit_app.py', 'r') as f:
    lines = f.readlines()

# The error lines are at the very bottom
# We need to remove the dangling else and except
new_lines = []
for i, line in enumerate(lines):
    if line.strip() == "else:" and lines[i+1].strip().startswith("st.error(f\"Analysis failed"):
        break  # We reached the dangling tail
    new_lines.append(line)

with open('streamlit_app.py', 'w') as f:
    f.writelines(new_lines)
