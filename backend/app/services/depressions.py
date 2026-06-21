from typing import Dict

import numpy as np
import pandas as pd
import rasterio
from scipy import ndimage

from app.services.dtm_processing import load_dtm


def _cell_area_from_meta(meta: dict) -> float:
    """Approximate cell area (m^2) from raster transform.

    Assumes square or near-square pixels in a projected CRS.
    """
    dx = meta["transform"][0]
    dy = abs(meta["transform"][4])
    return float(dx * dy)


def _segment_depressions(depth: np.ndarray, depth_threshold: float = 0.05):
    """Label contiguous depressed cells above a depth threshold.

    Returns (labels, num_labels).
    """
    mask = depth >= depth_threshold
    if not mask.any():
        return np.zeros_like(depth, dtype=np.int32), 0
    structure = np.ones((3, 3), dtype=bool)
    labels, nlab = ndimage.label(mask, structure=structure)
    return labels.astype(np.int32), int(nlab)


def analyze_depressions(outputs: Dict[str, str]) -> pd.DataFrame:
    """Analyze depressions using original and breached DTM plus SCA, slope, TWI.

    - Depression depth = max(dtm_breached - dtm_original, 0).
    - Segment contiguous depressions above a depth threshold.
    - For each depression, compute stats: depth, area, SCA, slope, TWI.
    - Derive a heuristic ponding-risk score and class.
    """
    original_path = outputs["dtm_original"]
    breached_path = outputs["dtm_breached"]
    sca_path = outputs["flow_accum_sca"]
    slope_path = outputs["slope_deg"]
    twi_path = outputs["twi"]

    original, meta = load_dtm(original_path)
    breached, _ = load_dtm(breached_path)
    depth = np.maximum(breached - original, 0.0)

    with rasterio.open(sca_path) as src_sca:
        sca = src_sca.read(1).astype("float32")
    with rasterio.open(slope_path) as src_slope:
        slope = src_slope.read(1).astype("float32")
    with rasterio.open(twi_path) as src_twi:
        twi = src_twi.read(1).astype("float32")

    # Basic validity mask
    mask = np.isfinite(depth) & np.isfinite(sca) & np.isfinite(slope) & np.isfinite(twi)
    if not mask.any():
        raise ValueError("No valid cells for depression analysis.")

    depth = np.where(mask, depth, 0.0)
    sca = np.where(mask, sca, 0.0)

    # Segment depressions
    labels, nlab = _segment_depressions(depth)
    if nlab == 0:
        # No significant depressions; return a single low-risk summary
        return pd.DataFrame(
            {
                "zone_id": ["field"],
                "mean_depth": [float(depth[mask].mean())],
                "max_depth": [float(depth[mask].max())],
                "area_m2": [float(mask.sum()) * _cell_area_from_meta(meta)],
                "mean_sca": [float(sca[mask].mean())],
                "max_sca": [float(sca[mask].max())],
                "mean_slope": [float(slope[mask].mean())],
                "mean_twi": [float(twi[mask].mean())],
                "risk_score": [0.0],
                "risk_label": ["Low"],
            }
        )

    cell_area = _cell_area_from_meta(meta)
    records = []

    # Normalization factors for risk scoring
    depth_max = float(depth.max() or 1.0)
    sca_max = float(sca.max() or 1.0)
    slope_max = float(slope[mask].max() or 1.0)
    twi_max = float(twi[mask].max() or 1.0)

    for lab in range(1, nlab + 1):
        m = labels == lab
        if not m.any():
            continue

        d_vals = depth[m]
        sca_vals = sca[m]
        slope_vals = slope[m]
        twi_vals = twi[m]
        area_m2 = float(m.sum()) * cell_area

        mean_depth = float(d_vals.mean())
        max_depth = float(d_vals.max())
        mean_sca = float(sca_vals.mean())
        max_sca = float(sca_vals.max())
        mean_slope = float(slope_vals.mean())
        mean_twi = float(twi_vals.mean())

        # Heuristic risk score: deeper, larger, flatter, wetter -> higher risk
        depth_norm = max_depth / depth_max
        sca_norm = max_sca / sca_max
        slope_norm = 1.0 - (mean_slope / slope_max) if slope_max > 0 else 1.0
        twi_norm = mean_twi / twi_max

        risk_score = 0.35 * depth_norm + 0.30 * sca_norm + 0.20 * slope_norm + 0.15 * twi_norm

        if risk_score < 0.3:
            risk_label = "Low"
        elif risk_score < 0.6:
            risk_label = "Medium"
        else:
            risk_label = "High"

        records.append(
            {
                "zone_id": f"depression_{lab}",
                "mean_depth": mean_depth,
                "max_depth": max_depth,
                "area_m2": area_m2,
                "mean_sca": mean_sca,
                "max_sca": max_sca,
                "mean_slope": mean_slope,
                "mean_twi": mean_twi,
                "risk_score": float(risk_score),
                "risk_label": risk_label,
            }
        )

    df = pd.DataFrame.from_records(records)
    # Sort highest-risk depressions first
    df = df.sort_values("risk_score", ascending=False).reset_index(drop=True)
    return df
