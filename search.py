from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import math

from utils import normalize
from utils import compute_frequency_weights, compute_recency_weight
from db import get_connection, load_resolved


# Modelo de embeddings para comparar texto
model = SentenceTransformer("all-MiniLM-L6-v2")


# Cache de dados e embeddings
RESOLVED = []
EMBEDDINGS = None
LAST_COUNT = -1

conn = get_connection()


# Recarrega dados e embeddings apenas quando necessário
def reload_if_needed():
    global RESOLVED, EMBEDDINGS, LAST_COUNT, FREQ

    data = load_resolved(conn)

    # Se não houve alterações, não faz reload
    if len(data) == LAST_COUNT:
        return

    print("Reloading embeddings from DB")

    RESOLVED = data
    LAST_COUNT = len(data)

    # Se não houver dados, limpa embeddings
    if not RESOLVED:
        EMBEDDINGS = None
        return

    # Garante que todos os tickets têm campo solution
    for item in RESOLVED:
        item.setdefault("solution", "")

    # Cria embeddings das descrições
    texts = [r["description"] for r in RESOLVED]
    EMBEDDINGS = model.encode(texts)

    # Calcula frequência das classificações
    FREQ = compute_frequency_weights(RESOLVED)


# Procura tickets semelhantes à descrição
def find_similar(description, top_k=5):

    reload_if_needed()

    # Se não houver dados ou embeddings, retorna vazio
    if not RESOLVED or EMBEDDINGS is None:
        return []

    # Embedding da nova descrição
    emb = model.encode([description])

    # Similaridade com todos os tickets
    similarities = cosine_similarity(emb, EMBEDDINGS)[0]

    results = []

    for i, item in enumerate(RESOLVED):

        # Similaridade textual
        sim_score = float(similarities[i])

        # Peso baseado na data
        recency_weight = compute_recency_weight(item.get("date"))

        # Chave de classificação
        key = (
            normalize(item["category"]),
            normalize(item["urgency"]),
            normalize(item["impact"]),
            normalize(item["priority"])
        )

        # Peso baseado na frequência
        freq = FREQ.get(key, 1)
        freq_weight = 1 + math.log(1 + freq)

        # Score final combina similaridade, frequência e recência
        final_score = sim_score * (0.7 * freq_weight + 0.3 * recency_weight)

        results.append({
            "ticket": item,  # 👈 SOLUTION vai aqui dentro
            "score": final_score,
            "raw_score": sim_score,
            "recency_weight": recency_weight,
            "freq_weight": freq_weight
        })

    # Ordena pelos melhores resultados
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    return results[:top_k]