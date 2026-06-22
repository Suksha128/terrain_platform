import rasterio
import glob

files = glob.glob('backend/results/5ed21a7a/*.tif')
for f in files:
    try:
        with rasterio.open(f) as src:
            print(f"{f.split('/')[-1]}: {src.shape}")
    except Exception as e:
        print(f"Error reading {f}: {e}")
