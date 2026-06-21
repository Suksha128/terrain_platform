import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from pathlib import Path
from typing import Dict


def reproject_raster(src_path: str, dst_path: str, dst_crs: str = "EPSG:32644") -> None:
    Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(src_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        profile = src.profile.copy()
        profile.update(crs=dst_crs, transform=transform, width=width, height=height)
        with rasterio.open(dst_path, "w", **profile) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.bilinear,
                )


def clip_raster_to_boundary(src_path: str, dst_path: str, boundary_geojson: Dict) -> None:
    shapes = [boundary_geojson]
    Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(src_path) as src:
        out_image, out_transform = mask(src, shapes, crop=True)
        out_profile = src.profile.copy()
        out_profile.update(
            height=out_image.shape[1],
            width=out_image.shape[2],
            transform=out_transform,
        )
        with rasterio.open(dst_path, "w", **out_profile) as dst:
            dst.write(out_image)
