import re

with open('backend/app/services/zoning.py', 'r') as f:
    content = f.read()

new_delineate = """def delineate_watersheds(flow_dir_path: str, flow_acc_path: str, output_dir: str, min_basin_size: int = None) -> str:
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    flow_dir_path = str(Path(flow_dir_path).resolve())
    flow_acc_path = str(Path(flow_acc_path).resolve())

    # Dynamically calculate threshold based on raster size
    import rasterio
    with rasterio.open(flow_acc_path) as src:
        total_pixels = src.width * src.height
        
    # Set stream threshold to 1% of total pixels, min 5, max 2000
    if min_basin_size is None:
        min_basin_size = max(5, min(2000, int(total_pixels * 0.01)))

    streams_path = str(out / "streams.tif")
    wbt.extract_streams(flow_accum=flow_acc_path, output=streams_path, threshold=min_basin_size, zero_background=False)

    watershed_path = str(out / "watersheds.tif")
    wbt.watershed(d8_pntr=flow_dir_path, pour_pts=streams_path, output=watershed_path, esri_pntr=False)
    
    # Check if watersheds were found, if not, fallback to simple basins
    with rasterio.open(watershed_path) as src:
        w_arr = src.read(1)
        if (w_arr > 0).sum() == 0:
            wbt.basins(d8_pntr=flow_dir_path, output=watershed_path)

    return watershed_path"""

content = re.sub(r'def delineate_watersheds.*?return watershed_path', new_delineate, content, flags=re.DOTALL)

with open('backend/app/services/zoning.py', 'w') as f:
    f.write(content)
