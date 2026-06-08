import datetime
import re
from collections import defaultdict

# Converte um score num nível de confiança legível para apresentar resultados ao utilizador
def get_confidence(score):
    if score > 0.85:
        return "High"
    elif score > 0.65:
        return "Medium"
    return "Low"


# Normaliza texto para facilitar comparações
def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text) 
    text = re.sub(r"\s+", " ", text).strip()
    return text


# Calcula peso com base na recência do incidente incidentes mais recentes têm mais peso
def compute_recency_weight(date_str):
    try:
        incident_date = datetime.datetime.fromisoformat(date_str)
        now = datetime.datetime.utcnow()

        age_days = (now - incident_date).days

        return 1 / (1 + age_days)

    except:
        return 1.0


# Calcula frequência das classificações no histórico
def compute_frequency_weights(resolved):
    counter = defaultdict(int)

    for r in resolved:
        key = (
            normalize(r["category"]),
            normalize(r["urgency"]),
            normalize(r["impact"]),
            normalize(r["priority"])
        )
        counter[key] += 1

    return counter
