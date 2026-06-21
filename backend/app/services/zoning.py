import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape
import whitebox
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from pathlib import Path
from app.utils.raster_utils import read_dtm, write_raster

wbt = whitebox.WhiteboxTools()
wbt.set_verbose_mode(False)


def delineate_watersheds(flow_dir_path: str, flow_acc_path: str, output_dir: str, min_basin_size: int = 500) -> str:
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    flow_dir_path = str(Path(flow_dir_path).resolve())
    flow_acc_path = str(Path(flow_acc_path).resolve())

    streams_path = str(out / "streams.tif")
    wbt.extract_streams(flow_accum=flow_acc_path, output=streams_path, threshold=min_basin_size, zero_background=False)

    watershed_path = str(out / "watersheds.tif")
    wbt.watershed(d8_pntr=flow_dir_path, pour_pts=streams_path, output=watershed_path, esri_pntr=False)
    return watershed_path


def create_terrain_clusters(feature_paths: dict, output_dir: str, n_clusters: int = 5) -> str:
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    feature_keys = ["slope", "twi", "elevation", "plan_curvature", "ndvi", "soil_moisture"]
    arrays = []
    ref_profile = None
    ref_shape = None

    for key in feature_keys:
        if key not in feature_paths:
            continue
        arr, profile = read_dtm(feature_paths[key])
        if ref_profile is None:
            ref_profile = profile
            ref_shape = arr.shape
        arrays.append(arr.flatten())

    if not arrays:
        raise ValueError("No feature arrays available for clustering.")

    X = np.stack(arrays, axis=1)
    valid_mask = ~np.any(np.isnan(X), axis=1)
    X_valid = X[valid_mask]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_valid)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)

    zone_flat = np.full(X.shape[0], -1, dtype=np.float32)
    zone_flat[valid_mask] = labels.astype(np.float32) + 1
    zone_arr = zone_flat.reshape(ref_shape)

    cluster_path = str(out / "terrain_clusters.tif")
    write_raster(cluster_path, zone_arr, ref_profile)
    return cluster_path


def create_combined_zones(flow_dir_path: str, flow_acc_path: str, feature_paths: dict, output_dir: str, n_clusters: int = 5, min_basin_size: int = 500) -> str:
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    watershed_path = delineate_watersheds(flow_dir_path, flow_acc_path, output_dir, min_basin_size)
    cluster_path = create_terrain_clusters(feature_paths, output_dir, n_clusters)

    arr_ws, profile = read_dtm(watershed_path)
    arr_cl, _ = read_dtm(cluster_path)

    arr_ws = np.nan_to_num(arr_ws, nan=0)
    arr_cl = np.nan_to_num(arr_cl, nan=0)
    combined = arr_ws.astype(np.int32) * 100 + arr_cl.astype(np.int32)
    combined = combined.astype(np.float32)
    combined[combined == 0] = np.nan

    combined_path = str(out / "zones_combined.tif")
    write_raster(combined_path, combined, profile)
    return combined_path


def zones_to_geodataframe(zone_raster_path: str) -> gpd.GeoDataFrame:
    with rasterio.open(zone_raster_path) as src:
        arr = src.read(1)
        transform = src.transform
        crs = src.crs

    mask = (arr > 0) & ~np.isnan(arr)
    geoms = [
        {"geometry": shape(geom), "zone_id": str(int(val))}
        for geom, val in shapes(arr.astype(np.float32), mask=mask, transform=transform)
    ]
    gdf = gpd.GeoDataFrame(geoms, crs=crs)
    gdf = gdf.dissolve(by="zone_id").reset_index()
    return gdf
