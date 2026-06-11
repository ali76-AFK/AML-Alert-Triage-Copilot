from fastapi import FastAPI, HTTPException

from app.models import AlertInput, AlertAnalysisOutput
from app.workflow import analyze_alert


app = FastAPI(title="AML Alert Triage Copilot")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AlertAnalysisOutput)
async def analyze(alert: AlertInput):
    try:
        result = await analyze_alert(alert)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
