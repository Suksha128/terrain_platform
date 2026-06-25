from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ZoneMethod(str, Enum):
    hydrologic = "hydrologic"
    terrain_cluster = "terrain_cluster"
    combined = "combined"


class ModelType(str, Enum):
    random_forest = "random_forest"
    xgboost = "xgboost"
    lightgbm = "lightgbm"


class AnalyzeRequest(BaseModel):
    job_id: str
    zone_method: ZoneMethod = ZoneMethod.combined
    n_clusters: int = Field(default=5, ge=2, le=20)
    model_type: ModelType = ModelType.xgboost
    fill_depressions: bool = True
    target_crs: str = "EPSG:32644"
    soil_type: str = "Loam"


class ZoneFeatures(BaseModel):
    zone_id: str
    mean_elevation: float
    mean_slope: float
    max_slope: float
    mean_aspect: float
    mean_curvature: float
    mean_twi: float
    max_flow_accumulation: float
    mean_depression_depth: float
    mean_ndvi: Optional[float] = None
    mean_chm: Optional[float] = None
    mean_soil_moisture: Optional[float] = None
    rainfall_total: Optional[float] = None


class RiskPrediction(BaseModel):
    zone_id: str
    waterlogging_risk: str
    risk_score: float
    drainage_priority: str
    irrigation_recommendation: str
    key_drivers: List[str]
    confidence: float


class AnalysisResult(BaseModel):
    job_id: str
    status: str
    zones: List[ZoneFeatures]
    predictions: List[RiskPrediction]
    zone_geojson_path: Optional[str] = None
    summary: Dict[str, Any] = {}


class TrainRequest(BaseModel):
    model_type: ModelType = ModelType.xgboost
    csv_path: str = Field(..., description="Path to your labeled zone CSV with waterlogging_risk column")


class TrainResponse(BaseModel):
    status: str
    model_type: str
    accuracy: float
    feature_importance: Dict[str, float]
