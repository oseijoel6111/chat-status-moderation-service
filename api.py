from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from pipeline import run_moderation

app = FastAPI(title="chat-status-moderation-service")


class ModerateRequest(BaseModel):
    path: str
    media_type: str | None = None


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/moderate")
def moderate(req: ModerateRequest):
    try:
        result = run_moderation(req.path, media_type=req.media_type)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "decision": result.decision.value,
        "max_score": result.max_score,
        "reason": result.decision_reason,
    }
