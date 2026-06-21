from pathlib import Path
from typing import Optional

import rasterio
from rasterio.warp import reproject, Resampling


def align_to_reference(
    src_path: str,
    ref_path: str,
    out_path: Optional[str] = None,
    resampling: str = "bilinear",
) -> str:
    """Reproject and resample src_path to match ref_path grid exactly.

    The output shares CRS, transform, width and height with the reference
    raster, so every (row, col) corresponds to the same ground location.
    """
    src_path = str(Path(src_path).resolve())
    ref_path = str(Path(ref_path).resolve())
    out_path = str(Path(out_path or src_path).resolve())

    with rasterio.open(ref_path) as ref:
        dst_crs = ref.crs
        dst_transform = ref.transform
        dst_height = ref.height
        dst_width = ref.width

    with rasterio.open(src_path) as src:
        dst_meta = src.meta.copy()
        dst_meta.update(
            {
                "crs": dst_crs,
                "transform": dst_transform,
                "width": dst_width,
                "height": dst_height,
            }
        )

        with rasterio.open(out_path, "w", **dst_meta) as dst:
            reproject(
                source=rasterio.band(src, 1),
                destination=rasterio.band(dst, 1),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=dst_transform,
                dst_crs=dst_crs,
                resampling=getattr(Resampling, resampling),
            )

    return out_path
