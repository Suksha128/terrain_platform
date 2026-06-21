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
        wbt.breach_depressions_least_cost(
            dem=working_dtm,
            output=filled_path,
            dist=5,
            min_dist=True,
            fill=True,
        )
        processed_dtm = filled_path
    else:
        processed_dtm = working_dtm

    return {
        "reprojected": reproj_path,
        "processed_dtm": processed_dtm,
    }
