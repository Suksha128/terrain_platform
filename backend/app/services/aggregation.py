import numpy as np
from typing import List
from app.models.schemas import ZoneFeatures
from app.utils.raster_utils import read_dtm


def compute_zonal_stats(zone_raster_path: str, feature_paths: dict, rainfall_total: float = None, ndvi_path: str = None, soil_moisture_path: str = None) -> List[ZoneFeatures]:
    zone_arr, _ = read_dtm(zone_raster_path)
    zone_ids = np.unique(zone_arr[~np.isnan(zone_arr)])

    feature_arrays = {}
    for name, path in feature_paths.items():
        arr, _ = read_dtm(path)
        feature_arrays[name] = arr

    if ndvi_path:
        feature_arrays["ndvi"], _ = read_dtm(ndvi_path)
    if soil_moisture_path:
        feature_arrays["soil_moisture"], _ = read_dtm(soil_moisture_path)

    results = []

    def stat(arr_name: str, mask, fn):
        if arr_name not in feature_arrays:
            return 0.0
        vals = feature_arrays[arr_name][mask]
        vals = vals[~np.isnan(vals)]
        return float(fn(vals)) if len(vals) > 0 else 0.0

    for zid in zone_ids:
        mask = zone_arr == zid
        results.append(ZoneFeatures(
            zone_id=str(int(zid)),
            mean_elevation=stat("elevation", mask, np.mean),
            mean_slope=stat("slope", mask, np.mean),
            max_slope=stat("slope", mask, np.max),
            mean_aspect=stat("aspect", mask, np.mean),
            mean_curvature=stat("plan_curvature", mask, np.mean),
            mean_twi=stat("twi", mask, np.mean),
            max_flow_accumulation=stat("flow_accumulation", mask, np.max),
            mean_depression_depth=stat("depression_depth", mask, np.mean),
            mean_ndvi=stat("ndvi", mask, np.mean) if "ndvi" in feature_arrays else None,
            mean_chm=stat("chm", mask, np.mean) if "chm" in feature_arrays else None,
            mean_soil_moisture=stat("soil_moisture", mask, np.mean) if "soil_moisture" in feature_arrays else None,
            rainfall_total=rainfall_total,
        ))

    return results
