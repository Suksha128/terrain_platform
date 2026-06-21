import json
import uuid
from pathlib import Path
from typing import List
import aiofiles
from fastapi import UploadFile, File, HTTPException, Form
from fastapi import APIRouter

from app.models.schemas import AnalyzeRequest, AnalysisResult, TrainRequest, TrainResponse
from app.services.dtm_preprocessing import preprocess_dtm
from app.services.terrain_features import extract_all_features
from app.services.zoning import delineate_watersheds, create_terrain_clusters, create_combined_zones, zones_to_geodataframe
from app.services.aggregation import compute_zonal_stats
from app.services.ml_pipeline import predict_risk, train_model
from app.services.insights import generate_insights

router = APIRouter()

UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")


@router.post("/upload/{feature_type}")
async def upload_feature(feature_type: str, job_id: str = None, file: UploadFile = File(...)):
    if not file.filename.endswith((".tif", ".tiff")):
        raise HTTPException(status_code=400, detail="Only GeoTIFF (.tif/.tiff) files accepted.")

    if not job_id:
        job_id = str(uuid.uuid4())[:8]
    dest = UPLOAD_DIR / f"{job_id}_{feature_type}.tif"
    UPLOAD_DIR.mkdir(exist_ok=True)

    async with aiofiles.open(dest, "wb") as f:
        content = await file.read()
        await f.write(content)

    return {"job_id": job_id, "feature_type": feature_type, "filename": file.filename, "path": str(dest)}


@router.post("/upload_folder")
async def upload_folder(job_id: str = Form(None), files: List[UploadFile] = File(...)):
    if not job_id:
        job_id = str(uuid.uuid4())[:8]
        
    UPLOAD_DIR.mkdir(exist_ok=True)
    mapped_features = []
    
    for file in files:
        if not file.filename.endswith((".tif", ".tiff")):
            continue
            
        fname = file.filename.lower()
        feature_type = "unknown"
        if "dtm" in fname or "dem" in fname:
            feature_type = "dtm"
        elif "ndvi" in fname:
            feature_type = "ndvi"
        elif "slope" in fname:
            feature_type = "slope"
        elif "aspect" in fname:
            feature_type = "aspect"
        elif "twi" in fname:
            feature_type = "twi"
        elif "flow" in fname and "dir" in fname:
            feature_type = "flow_direction"
        elif "flow" in fname and "acc" in fname:
            feature_type = "flow_accumulation"
        elif "watershed" in fname or "basin" in fname:
            feature_type = "watersheds"
        elif "soil" in fname and "moist" in fname:
            feature_type = "soil_moisture"
            
        if feature_type != "unknown":
            dest = UPLOAD_DIR / f"{job_id}_{feature_type}.tif"
            async with aiofiles.open(dest, "wb") as f:
                content = await file.read()
                await f.write(content)
            mapped_features.append(feature_type)
            
    if "dtm" not in mapped_features:
        raise HTTPException(status_code=400, detail="No DTM/DEM file found in the uploaded folder.")
        
    return {"job_id": job_id, "mapped_features": mapped_features}


@router.post("/analyze", response_model=AnalysisResult)
def analyze(req: AnalyzeRequest):
    dtm_path = UPLOAD_DIR / f"{req.job_id}_dtm.tif"
    if not dtm_path.exists():
        raise HTTPException(status_code=404, detail="DTM file not found for this job_id.")

    job_dir = str(RESULTS_DIR / req.job_id)
    Path(job_dir).mkdir(parents=True, exist_ok=True)

    prep = preprocess_dtm(str(dtm_path), job_dir, target_crs=req.target_crs, fill_depressions=req.fill_depressions)
    processed_dtm = prep["processed_dtm"]

    pre_uploaded = {}
    for ft in ["slope", "aspect", "twi", "flow_direction", "flow_accumulation", "depression_depth", "watersheds", "ndvi", "soil_moisture"]:
        f_path = UPLOAD_DIR / f"{req.job_id}_{ft}.tif"
        if f_path.exists():
            pre_uploaded[ft] = str(f_path.resolve())

    feat_paths = extract_all_features(processed_dtm, job_dir, pre_uploaded)

    from app.utils.geo_utils import align_raster_to_reference
    # Make sure optional features are still passed into compute_zonal_stats
    for opt in ["ndvi", "soil_moisture", "watersheds"]:
        if opt in pre_uploaded and opt not in feat_paths:
            aligned_path = str(Path(job_dir) / f"{opt}_aligned.tif")
            align_raster_to_reference(pre_uploaded[opt], processed_dtm, aligned_path)
            feat_paths[opt] = aligned_path

    if req.zone_method == req.zone_method.hydrologic:
        zone_path = delineate_watersheds(feat_paths["flow_direction"], feat_paths["flow_accumulation"], job_dir)
    elif req.zone_method == req.zone_method.terrain_cluster:
        zone_path = create_terrain_clusters(feat_paths, job_dir, req.n_clusters)
    else:
        zone_path = create_combined_zones(feat_paths["flow_direction"], feat_paths["flow_accumulation"], feat_paths, job_dir, req.n_clusters)

    gdf = zones_to_geodataframe(zone_path)
    geojson_path = str(Path(job_dir) / "zones.geojson")
    gdf.to_file(geojson_path, driver="GeoJSON")

    zones = compute_zonal_stats(zone_path, feat_paths)

    predictions = predict_risk(zones)

    insights = generate_insights(zones, predictions)

    result_path = Path(job_dir) / "results.json"
    with open(result_path, "w") as f:
        json.dump(insights, f, indent=2)

    return AnalysisResult(
        job_id=req.job_id,
        status="completed",
        zones=zones,
        predictions=predictions,
        zone_geojson_path=geojson_path,
        summary=insights,
    )


@router.get("/results/{job_id}")
def get_results(job_id: str):
    result_path = RESULTS_DIR / job_id / "results.json"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Results not found.")
    with open(result_path) as f:
        return json.load(f)


@router.get("/zones/{job_id}")
def get_zones_geojson(job_id: str):
    geojson_path = RESULTS_DIR / job_id / "zones.geojson"
    if not geojson_path.exists():
        raise HTTPException(status_code=404, detail="Zone GeoJSON not found.")
    with open(geojson_path) as f:
        return json.load(f)


@router.get("/insights/{job_id}")
def get_insights(job_id: str):
    result_path = RESULTS_DIR / job_id / "results.json"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Insights not found.")
    with open(result_path) as f:
        data = json.load(f)
    return data.get("zones", [])


@router.post("/train", response_model=TrainResponse)
def train(req: TrainRequest):
    result = train_model(csv_path=req.csv_path, model_type=req.model_type)
    return TrainResponse(
        status="trained",
        model_type=result["model_type"],
        accuracy=result["accuracy"],
        feature_importance=result["feature_importance"],
    )
