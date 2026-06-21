import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from pathlib import Path
from typing import Dict
import numpy as np


def reproject_raster(src_path: str, dst_path: str, dst_crs: str = "EPSG:32644") -> None:
    Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(src_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        profile = src.profile.copy()
        profile.pop('tiled', None)
        profile.pop('blockxsize', None)
        profile.pop('blockysize', None)
        profile.pop('compress', None)
        
        nodata = src.nodata if src.nodata is not None else -9999.0
        profile.update(crs=dst_crs, transform=transform, width=width, height=height, nodata=nodata)
        
        with rasterio.open(dst_path, "w", **profile) as dst:
            for i in range(1, src.count + 1):
                band = src.read(i)
                # Replace NaNs with nodata if they exist
                if np.isnan(band).any():
                    band[np.isnan(band)] = nodata
                    
                reproject(
                    source=band,
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    src_nodata=nodata,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    dst_nodata=nodata,
                    resampling=Resampling.bilinear,
                )


def clip_raster_to_boundary(src_path: str, dst_path: str, boundary_geojson: Dict) -> None:
    shapes = [boundary_geojson]
    Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(src_path) as src:
        nodata = src.nodata if src.nodata is not None else -9999.0
        out_image, out_transform = mask(src, shapes, crop=True, nodata=nodata, filled=True)
        
        # Ensure NaNs are replaced
        if np.isnan(out_image).any():
            out_image[np.isnan(out_image)] = nodata
            
        out_profile = src.profile.copy()
        out_profile.pop('tiled', None)
        out_profile.pop('blockxsize', None)
        out_profile.pop('blockysize', None)
        out_profile.pop('compress', None)
        out_profile.update(
            height=out_image.shape[1],
            width=out_image.shape[2],
            transform=out_transform,
            nodata=nodata
        )
        with rasterio.open(dst_path, "w", **out_profile) as dst:
            dst.write(out_image)

def align_raster_to_reference(src_path: str, ref_path: str, dst_path: str) -> None:
    """Reprojects and resamples src_path to exactly match the shape, crs, and transform of ref_path."""
    from rasterio.warp import reproject, Resampling
    
    with rasterio.open(ref_path) as ref:
        ref_crs = ref.crs
        ref_transform = ref.transform
        ref_width = ref.width
        ref_height = ref.height
        ref_profile = ref.profile.copy()
        
    with rasterio.open(src_path) as src:
        src_nodata = src.nodata if src.nodata is not None else -9999.0
        ref_nodata = ref.nodata if ref.nodata is not None else -9999.0
        
        out_profile = ref_profile.copy()
        out_profile.update(
            dtype=src.profile['dtype'],
            nodata=src_nodata,
            count=src.count
        )
        
        out_profile.pop('tiled', None)
        out_profile.pop('blockxsize', None)
        out_profile.pop('blockysize', None)
        out_profile.pop('compress', None)
        
        with rasterio.open(dst_path, 'w', **out_profile) as dst:
            for i in range(1, src.count + 1):
                band = src.read(i)
                if np.isnan(band).any():
                    band[np.isnan(band)] = src_nodata
                    
                reproject(
                    source=band,
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    src_nodata=src_nodata,
                    dst_transform=ref_transform,
                    dst_crs=ref_crs,
                    dst_nodata=src_nodata,
                    resampling=Resampling.bilinear,
                )
