from pathlib import Path
from typing import Dict, Optional

import numpy as np
import rasterio

try:
    import whitebox  # type: ignore
    from whitebox.whitebox_tools import WhiteboxTools  # type: ignore
except Exception:  # library optional at runtime
    whitebox = None
    WhiteboxTools = None  # type: ignore


def load_dtm(path: str):
    """Load a DEM/DTM raster into a NumPy array and preserve metadata."""
    with rasterio.open(path) as src:
        dtm = src.read(1).astype("float32")
        meta = src.meta.copy()
    return dtm, meta


def save_raster(path: str, arr, meta):
    """Save a single-band float32 raster with existing metadata."""
    meta = meta.copy()
    meta.update(dtype="float32", count=1)
    with rasterio.open(path, "w", **meta) as dst:
        dst.write(arr.astype("float32"), 1)


def _get_wbt(working_dir: str):
    """Return a configured WhiteboxTools instance or raise if unavailable."""
    if WhiteboxTools is None:
        raise ImportError(
            "whitebox / WhiteboxTools is not installed. "
            "See https://whitebox.readthedocs.io/en/latest/usage.html"
        )
    wbt = WhiteboxTools()
    wbt.set_working_dir(working_dir)
    wbt.verbose = False
    return wbt


def preprocess_dtm_with_whitebox(
    dtm_path: str,
    work_dir: Optional[str] = None,
    denoise: bool = True,
) -> Dict[str, str]:
    """Preprocess a DTM and derive hydrological rasters using WhiteboxTools.

    Expects a *terrain* (bare-earth) elevation model in a projected metric CRS.

    Returns a dict with paths to:
    - dtm_original: original input DTM
    - dtm_breached: hydrologically corrected DTM
    - flow_pointer: flow direction (D8 pointer)
    - flow_accum_sca: specific contributing area
    - slope_deg: slope in degrees
    - twi: topographic wetness index
    """
    dtm_path = str(Path(dtm_path).resolve())
    wd = Path(work_dir or Path(dtm_path).parent).resolve()
    wd.mkdir(parents=True, exist_ok=True)
    wbt = _get_wbt(str(wd))

    # Preserve original DTM path
    dtm_original = wd / "dtm_original.tif"
    # Copy original into working dir for traceability
    if Path(dtm_path) != dtm_original:
        with rasterio.open(dtm_path) as src:
            arr = src.read(1)
            meta = src.meta.copy()
        save_raster(str(dtm_original), arr, meta)

    # Optional smoothing to reduce noise while keeping edges
    smoothed = wd / "dtm_smoothed.tif"
    if denoise:
        wbt.feature_preserving_denoise(dem=str(dtm_original), output=str(smoothed), filter=9)
        dtm_in = str(smoothed)
    else:
        dtm_in = str(dtm_original)

    # Flow accumulation workflow: breach depressions, pointer, SCA
    out_dtm = wd / "dtm_breached.tif"
    out_pntr = wd / "flow_pointer.tif"
    out_accum = wd / "flow_accum_sca.tif"
    wbt.flow_accumulation_full_workflow(
        dem=dtm_in,
        out_dem=str(out_dtm),
        out_pntr=str(out_pntr),
        out_accum=str(out_accum),
        out_type="sca",
        log=False,
    )

    # Slope in degrees from breached DTM
    slope = wd / "slope_deg.tif"
    wbt.slope(dem=str(out_dtm), output=str(slope), units="degrees", zfactor=1.0)

    # TWI from SCA and slope
    twi = wd / "twi.tif"
    try:
        wbt.wetness_index(sca=str(out_accum), slope=str(slope), output=str(twi))
    except Exception:
        with rasterio.open(out_accum) as src_acc, rasterio.open(slope) as src_slope:
            sca_arr = src_acc.read(1).astype("float32")
            slope_arr = src_slope.read(1).astype("float32")
            slope_rad = np.radians(np.clip(slope_arr, 0.1, None))
            twi_arr = np.log(np.clip(sca_arr, 1e-3, None) / np.tan(slope_rad))
            meta = src_acc.meta.copy()
        save_raster(str(twi), twi_arr, meta)

    return {
        "dtm_original": str(dtm_original),
        "dtm_breached": str(out_dtm),
        "flow_pointer": str(out_pntr),
        "flow_accum_sca": str(out_accum),
        "slope_deg": str(slope),
        "twi": str(twi),
    }
