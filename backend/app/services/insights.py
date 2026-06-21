from typing import List, Dict, Any
from app.models.schemas import ZoneFeatures, RiskPrediction


def generate_insights(zones: List[ZoneFeatures], predictions: List[RiskPrediction]) -> Dict[str, Any]:
    pred_map = {p.zone_id: p for p in predictions}

    zone_insights = []
    for z in zones:
        p = pred_map.get(z.zone_id)
        if not p:
            continue
        zone_insights.append({
            "zone_id": z.zone_id,
            "risk_level": p.waterlogging_risk,
            "risk_score": round(p.risk_score, 3),
            "confidence": round(p.confidence, 3),
            "terrain_summary": _terrain_summary(z),
            "why_at_risk": p.key_drivers,
            "actions": _recommended_actions(p, z),
            "drainage_priority": p.drainage_priority,
            "irrigation": p.irrigation_recommendation,
            "metrics": {
                "mean_slope_deg": round(z.mean_slope, 2),
                "mean_twi": round(z.mean_twi, 2),
                "max_flow_acc": round(z.max_flow_accumulation, 0),
                "depression_depth_m": round(z.mean_depression_depth, 3),
                "mean_elevation_m": round(z.mean_elevation, 1),
            },
        })

    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    for p in predictions:
        risk_counts[p.waterlogging_risk] = risk_counts.get(p.waterlogging_risk, 0) + 1

    critical_zones = [p.zone_id for p in predictions if p.drainage_priority == "Critical"]

    summary = {
        "total_zones": len(zones),
        "risk_distribution": risk_counts,
        "critical_zones": critical_zones,
        "field_status": _field_status(risk_counts),
        "top_priority_action": _top_action(risk_counts, critical_zones),
        "zones": zone_insights,
    }
    return summary


def _terrain_summary(z: ZoneFeatures) -> str:
    slope_desc = (
        "nearly flat" if z.mean_slope < 1.0 else
        "gently sloped" if z.mean_slope < 3.0 else
        "moderately sloped" if z.mean_slope < 7.0 else "steeply sloped"
    )
    wet_desc = (
        "highly wet" if z.mean_twi > 12 else
        "moderately wet" if z.mean_twi > 8 else "relatively dry"
    )
    return f"{slope_desc.capitalize()} terrain at {z.mean_elevation:.0f} m elevation, {wet_desc} (TWI {z.mean_twi:.1f})."


def _recommended_actions(p: RiskPrediction, z: ZoneFeatures):
    actions = []
    if p.waterlogging_risk == "High":
        actions.append("Install sub-surface tile drains or open field drains immediately.")
        actions.append("Avoid tillage when soil is saturated to prevent compaction.")
        if z.mean_depression_depth > 0.3:
            actions.append("Consider land leveling to reduce depression storage.")
    elif p.waterlogging_risk == "Medium":
        actions.append("Monitor soil moisture weekly during monsoon season.")
        actions.append("Consider raised bed cultivation for sensitive crops.")
    else:
        actions.append("Standard field management applies; no urgent drainage intervention.")

    if z.max_flow_accumulation > 10000:
        actions.append("Install diversion channels to intercept upslope runoff.")
    if z.mean_slope < 0.5:
        actions.append("Improve surface grading to create minimum 0.5% drainage slope.")
    return actions


def _field_status(counts: Dict[str, int]) -> str:
    total = sum(counts.values())
    if total == 0:
        return "Unknown"
    high_pct = counts.get("High", 0) / total
    if high_pct > 0.5:
        return "Critical — majority of field at high waterlogging risk"
    if high_pct > 0.25:
        return "Moderate — significant portions at risk"
    return "Healthy — most zones low-medium risk"


def _top_action(counts: Dict[str, int], critical: list) -> str:
    if counts.get("High", 0) > 0:
        return f"Prioritise drainage infrastructure in {len(critical)} critical zone(s) before next irrigation cycle."
    if counts.get("Medium", 0) > 0:
        return "Monitor medium-risk zones closely; prepare contingency drainage plans."
    return "No immediate action required; routine monitoring recommended."
