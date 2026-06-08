import json
import time
import os
from search import find_similar
from decision import decide_classification
from utils import get_confidence
from db import get_connection, insert_incident, clear_incidents

# Cria ligação à base de dados
conn = get_connection()

# Limpa a tabela temporária no início da execução
clear_incidents(conn)

# Lê os incidentes a processar a partir de um ficheiro JSON
with open("data.json", "r", encoding="utf-8") as f:
    incidents = json.load(f)["incidents"]

# Processa cada incidente individualmente
for incident in incidents:

    print(f"\nProcessing incident {incident['id']}")
    print(f"Description: {incident['description']}")

    start = time.time()

    # Pesquisa os casos mais semelhantes na base de dados
    top_k = find_similar(incident["description"], top_k=5)

    # Decide a classificação final (categoria, urgência, etc.)
    classification, best_score, voted_category, mode = decide_classification(
        incident["description"],
        top_k
    )

    end = time.time()

    print("\nFinal Classification:")
    print(f"Category: {classification.get('category','')}")
    print(f"Urgency: {classification.get('urgency','')}")
    print(f"Impact: {classification.get('impact','')}")
    print(f"Priority: {classification.get('priority','')}")
    print(f"Solution: {classification.get('solution','')}") 

    # Converte score em confiança
    print(f"Confidence: {get_confidence(best_score)}")

    # Tempo de execução
    print(f"Execution time: {round(end-start,2)} seconds")

    print("-" * 50)

    # Guarda o incidente na base de dados
    insert_incident(conn, {
        "id": incident["id"],
        "description": incident["description"],
        "prediction": {
            "category": classification.get("category"),
            "urgency": classification.get("urgency"),
            "impact": classification.get("impact"),
            "priority": classification.get("priority"),
            "solution": classification.get("solution") 
        },
        "confidence": best_score,
        "mode": mode,
        "top_k": top_k
    })

# Fecha ligação
conn.close()

# Abre a interface para feedback (NÃO ALTERADO)
print("\nOpening feedback UI...")
os.system("python ui.py")