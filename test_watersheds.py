import asyncio
from app.api.routes import analyze
from app.models.schemas import AnalyzeRequest
import pytest

async def test():
    req = AnalyzeRequest(job_id="5ed21a7a", target_crs="EPSG:32644", zone_method="hydrologic", fill_depressions=True, model_type="random_forest")
    res = await analyze(req)
    print("Result:", res)

asyncio.run(test())
