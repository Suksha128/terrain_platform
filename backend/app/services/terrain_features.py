import os
import tempfile
import numpy as np
import whitebox
from pathlib import Path
from app.utils.raster_utils import read_dtm, write_raster

wbt = whitebox.WhiteboxTools()
wbt.set_verbose_mode(False)


def extract_all_features(dtm_path: str, output_dir: str, pre_uploaded: dict = None) -> dict:
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    dtm_path = str(Path(dtm_path).resolve())

    if pre_uploaded is None:
        pre_uploaded = {}

    paths = {}

    conditioned_dtm_path = str(out / "conditioned_dtm.tif")
    if "conditioned_dtm" in pre_uploaded:
        paths["conditioned_dtm"] = pre_uploaded["conditioned_dtm"]
    else:
        wbt.breach_depressions(dem=dtm_path, output=conditioned_dtm_path)
        paths["conditioned_dtm"] = conditioned_dtm_path

    slope_path = str(out / "slope.tif")
    if "slope" in pre_uploaded:
        paths["slope"] = pre_uploaded["slope"]
    else:
        wbt.slope(dem=paths["conditioned_dtm"], output=slope_path, zfactor=1.0, units="degrees")
        paths["slope"] = slope_path

    aspect_path = str(out / "aspect.tif")
    if "aspect" in pre_uploaded:
        paths["aspect"] = pre_uploaded["aspect"]
    else:
        wbt.aspect(dem=paths["conditioned_dtm"], output=aspect_path)
        paths["aspect"] = aspect_path

    profile_curv_path = str(out / "profile_curvature.tif")
    if "profile_curvature" in pre_uploaded:
        paths["profile_curvature"] = pre_uploaded["profile_curvature"]
    else:
        wbt.profile_curvature(dem=paths["conditioned_dtm"], output=profile_curv_path)
        paths["profile_curvature"] = profile_curv_path

    plan_curv_path = str(out / "plan_curvature.tif")
    if "plan_curvature" in pre_uploaded:
        paths["plan_curvature"] = pre_uploaded["plan_curvature"]
    else:
        wbt.plan_curvature(dem=paths["conditioned_dtm"], output=plan_curv_path)
        paths["plan_curvature"] = plan_curv_path

    flow_dir_path = str(out / "flow_direction.tif")
    if "flow_direction" in pre_uploaded:
        paths["flow_direction"] = pre_uploaded["flow_direction"]
    else:
        wbt.d8_pointer(dem=paths["conditioned_dtm"], output=flow_dir_path, esri_pntr=False)
        paths["flow_direction"] = flow_dir_path

    # Calculate D8 for Stream Extraction & Basins (requires cell counts)
    flow_acc_path = str(out / "flow_accumulation.tif")
    if "flow_accumulation" in pre_uploaded:
        paths["flow_accumulation"] = pre_uploaded["flow_accumulation"]
    else:
        wbt.d8_flow_accumulation(
            i=paths["conditioned_dtm"],
            output=flow_acc_path,
            out_type="cells",
            log=False,
            clip=False
        )
        paths["flow_accumulation"] = flow_acc_path

    # ADVANCED ACCURACY: Calculate D-Infinity SCA exclusively for highly accurate TWI
    d_inf_sca_path = str(out / "d_inf_sca.tif")
    wbt.d_inf_flow_accumulation(
        i=paths["conditioned_dtm"],
        output=d_inf_sca_path,
        out_type="sca",
        log=False,
        clip=False,
        pntr=False
    )
    paths["d_inf_sca"] = d_inf_sca_path

    twi_path = str(out / "twi.tif")
    if "twi" in pre_uploaded:
        paths["twi"] = pre_uploaded["twi"]
    else:
        wbt.wetness_index(
            sca=paths["d_inf_sca"],
            slope=paths["slope"],
            output=twi_path,
        )
        paths["twi"] = twi_path

    depression_path = str(out / "depression_depth.tif")
    if "depression_depth" in pre_uploaded:
        paths["depression_depth"] = pre_uploaded["depression_depth"]
    else:
        _compute_depression_depth(dtm_path, depression_path)
        paths["depression_depth"] = depression_path

    paths["elevation"] = dtm_path

    # Advanced Analysis: Canopy Height Model (CHM)
    if "dem" in pre_uploaded:
        # Assuming the DEM has already been aligned to the DTM by routes.py
        chm_path = str(out / "chm.tif")
        wbt.subtract(input1=pre_uploaded["dem"], input2=dtm_path, output=chm_path)
        
        # Ensure CHM is non-negative (noise can cause DEM < DTM)
        arr_chm, profile = read_dtm(chm_path)
        arr_chm = np.maximum(arr_chm, 0.0)
        write_raster(chm_path, arr_chm, profile)
        
        paths["chm"] = chm_path

    return paths


def _compute_depression_depth(dtm_path: str, output_path: str) -> None:
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
        pass