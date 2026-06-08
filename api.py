# api.py

from fastapi import FastAPI
from pydantic import BaseModel

from search import find_similar
from decision import decide_classification
from utils import get_confidence

app = FastAPI()


# ---------- REQUEST MODEL ----------
class IncidentRequest(BaseModel):
    description: str


# ---------- HEALTH CHECK ----------
@app.get("/")
def root():
    return {"status": "API is running"}


# ---------- MAIN ENDPOINT ----------
@app.post("/classify")
def classify_incident_api(data: IncidentRequest):

    description = data.description

    # procura semelhantes
    top_k = find_similar(description, top_k=5)

    # decide classificação
    classification, best_score, voted_category, mode = decide_classification(
        description,
        top_k
    )

    return {
        "category": classification.get("category"),
        "urgency": classification.get("urgency"),
        "impact": classification.get("impact"),
        "priority": classification.get("priority"),
        "solution": classification.get("solution"),
        "confidence": best_score,
        "confidence_label": get_confidence(best_score),
        "mode": mode
    }