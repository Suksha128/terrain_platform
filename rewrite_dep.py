def rewrite_file():
    with open('backend/app/services/terrain_features.py', 'r') as f:
        content = f.read()
    
    new_func = """def _compute_depression_depth(dtm_path: str, output_path: str) -> None:
    import numpy as np
    import tempfile, os
    from app.utils.raster_utils import read_dtm, write_raster
    arr_orig, profile = read_dtm(dtm_path)

    tmp_filled = tempfile.mktemp(suffix=".tif")
    wbt.fill_depressions(dem=dtm_path, output=tmp_filled, fix_flats=True)
    
    if not Path(tmp_filled).exists():
        print(f"WARNING: WBT failed to fill depressions for depth. Outputting zeros at {output_path}")
        zeros = np.zeros_like(arr_orig, dtype=np.float32)
        write_raster(output_path, zeros, profile)
        return

    arr_filled, _ = read_dtm(tmp_filled)

    depth = np.where(
        np.isnan(arr_orig) | np.isnan(arr_filled),
        np.nan,
        arr_filled - arr_orig,
    )
    depth = np.maximum(depth, 0.0)
    write_raster(output_path, depth, profile)

    try:
        os.remove(tmp_filled)
    except Exception:
        pass"""
    
    import re
    # We replace from "def _compute_depression_depth" to the end of the try/except block.
    content = re.sub(r'def _compute_depression_depth\(.*?\).*?except Exception:\s*pass', new_func, content, flags=re.DOTALL)
    
    with open('backend/app/services/terrain_features.py', 'w') as f:
        f.write(content)

rewrite_file()
