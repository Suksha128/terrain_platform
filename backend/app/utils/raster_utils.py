import numpy as np
import rasterio
from rasterio.enums import Resampling
from pathlib import Path
from typing import Tuple


def read_dtm(path: str) -> Tuple[np.ndarray, dict]:
    with rasterio.open(path) as src:
        arr = src.read(1).astype(np.float32)
        profile = src.profile.copy()
        nodata = src.nodata
    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)
    return arr, profile


def write_raster(path: str, array: np.ndarray, profile: dict, nodata: float = -9999.0) -> None:
    profile = profile.copy()
    profile.update(dtype=rasterio.float32, count=1, nodata=nodata)
    array = np.where(np.isnan(array), nodata, array).astype(np.float32)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(array, 1)


def get_cell_size(profile: dict) -> float:
    return abs(profile["transform"].a)


def normalize_array(arr: np.ndarray) -> np.ndarray:
    mn, mx = np.nanmin(arr), np.nanmax(arr)
    if mx == mn:
        return np.zeros_like(arr)
    return (arr - mn) / (mx - mn)
