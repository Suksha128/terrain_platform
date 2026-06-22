import re

with open('backend/app/services/ml_pipeline.py', 'r') as f:
    content = f.read()

rule_patch = """        if z.max_flow_accumulation > 10000:
            score += 0.1
            
        # Factor in live weather forecast
        if z.rainfall_total and z.rainfall_total > 20:
            score += 0.25
        elif z.rainfall_total and z.rainfall_total > 5:
            score += 0.1"""

content = content.replace('        if z.max_flow_accumulation > 10000:\n            score += 0.1', rule_patch)

with open('backend/app/services/ml_pipeline.py', 'w') as f:
    f.write(content)
