import whitebox
from pathlib import Path
from typing import Dict, Optional
from app.utils.geo_utils import reproject_raster, clip_raster_to_boundary

wbt = whitebox.WhiteboxTools()
wbt.set_verbose_mode(True)


def preprocess_dtm(
    input_path: str,
    output_dir: str,
    target_crs: str = "EPSG:32644",
    fill_depressions: bool = True,
    boundary_geojson: Optional[Dict] = None,
) -> Dict[str, str]:
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    input_path = str(Path(input_path).resolve())

    reproj_path = str(out / "dtm_reproj.tif")
    reproject_raster(input_path, reproj_path, target_crs)

    if boundary_geojson is not None:
        clipped_path = str(out / "dtm_clipped.tif")
        clip_raster_to_boundary(reproj_path, clipped_path, boundary_geojson)
        working_dtm = clipped_path
    else:
        working_dtm = reproj_path

    if fill_depressions:
        filled_path = str(out / "dtm_filled.tif")
        wbt.fill_depressions(
            dem=working_dtm,
            output=filled_path,
            fix_flats=True
        )
        if Path(filled_path).exists():
            processed_dtm = filled_path
        else:
            print("WARNING: WBT failed to fill depressions. Falling back to working DTM.")
            processed_dtm = working_dtm
    else:
        processed_dtm = working_dtm

    return {
        "reprojected": reproj_path,
        "processed_dtm": processed_dtm,
    }
