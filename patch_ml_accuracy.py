import re

with open('backend/app/services/ml_pipeline.py', 'r') as f:
    content = f.read()

advanced_rules = """        # Factor in live weather forecast
        if z.rainfall_total and z.rainfall_total > 20:
            score += 0.25
        elif z.rainfall_total and z.rainfall_total > 5:
            score += 0.1
            
        # ADVANCED ACCURACY: Ground Truth integration (NDVI / Moisture)
        if z.mean_ndvi is not None:
            if z.mean_ndvi < 0.2 and z.mean_twi > 10:
                # Vegetation is dead in a wet sink -> Extreme Waterlogging
                score += 0.4
            elif z.mean_ndvi > 0.6:
                # Highly healthy vegetation -> Lower Risk
                score -= 0.15
                
        if z.mean_soil_moisture is not None:
            if z.mean_soil_moisture > 0.8:
                score += 0.3
            elif z.mean_soil_moisture < 0.3:
                score -= 0.2
"""

content = content.replace('        # Factor in live weather forecast\n        if z.rainfall_total and z.rainfall_total > 20:\n            score += 0.25\n        elif z.rainfall_total and z.rainfall_total > 5:\n            score += 0.1', advanced_rules)

with open('backend/app/services/ml_pipeline.py', 'w') as f:
    f.write(content)
