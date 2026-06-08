from classifier import classify_incident
from utils import normalize

# Limiares que controlam a confiança do sistema
HIGH_THRESHOLD = 0.75
MID_THRESHOLD = 0.40


# Seleciona o ticket mais recente
def pick_most_recent(tickets):
    return sorted(
        tickets,
        key=lambda x: x["ticket"].get("date", ""),
        reverse=True
    )[0]


# Votação ponderada sobre os tickets semelhantes
def weighted_decision(top_k):
    scores = {}

    for item in top_k:
        ticket = item["ticket"]

        key = (
            normalize(ticket["category"]),
            normalize(ticket["urgency"]),
            normalize(ticket["impact"]),
            normalize(ticket["priority"]),
            ticket.get("solution", "")
        )

        scores[key] = scores.get(key, 0) + item["score"]

    best = max(scores, key=scores.get)

    return {
        "category": best[0],
        "urgency": best[1],
        "impact": best[2],
        "priority": best[3],
        "solution": best[4]
    }


# Função principal de decisão
def decide_classification(description, top_k):

    # 1. LLM PURO sem contexto
    if not top_k:
        print("\n[MODE] LLM (no data)")
        llm = classify_incident(description)
        llm.setdefault("solution", "")
        return llm, 0.0, "llm", "llm"

    best_score = top_k[0]["score"]

    print(f"\n[DEBUG] Best score: {round(best_score, 4)}")
    print(f"[DEBUG] Thresholds → MID: {MID_THRESHOLD} | HIGH: {HIGH_THRESHOLD}")

    # 2. EXACT MATCH
    exact = [t for t in top_k if t["raw_score"] > 0.99]

    if exact:
        print("[MODE] DB (exact match)")

        if len(exact) == 1:
            result = exact[0]
        else:
            print("[MODE] DB (conflict → most recent)")
            result = pick_most_recent(exact)

        ticket = result["ticket"]

        return {
            "category": ticket["category"],
            "urgency": ticket["urgency"],
            "impact": ticket["impact"],
            "priority": ticket["priority"],
            "solution": ticket.get("solution", "")
        }, 1.0, "exact", "db"

    # 3. HIGH CONFIDENCE
    if best_score > HIGH_THRESHOLD:
        print(f"[MODE] DB (strong match > {HIGH_THRESHOLD})")

        ticket = top_k[0]["ticket"]

        return {
            "category": ticket["category"],
            "urgency": ticket["urgency"],
            "impact": ticket["impact"],
            "priority": ticket["priority"],
            "solution": ticket.get("solution", "")
        }, best_score, "strong", "db"

    # 4. MID → RAG
    if best_score > MID_THRESHOLD:
        print(f"[MODE] HYBRID (RAG)")

        llm = classify_incident(description, context_tickets=top_k)

        if "error" not in llm:
            print("[MODE] HYBRID → LLM success")
            llm.setdefault("solution", "")
            return llm, best_score, "hybrid", "llm"

        print("[MODE] HYBRID → fallback DB")
        return weighted_decision(top_k), best_score, "fallback", "db"

    # 5. LOW → LLM
    print(f"[MODE] LLM (low similarity < {MID_THRESHOLD})")

    llm = classify_incident(description)

    if "error" in llm:
        print("[MODE] LLM failed → fallback DB")

        ticket = top_k[0]["ticket"]

        return {
            "category": ticket["category"],
            "urgency": ticket["urgency"],
            "impact": ticket["impact"],
            "priority": ticket["priority"],
            "solution": ticket.get("solution", "")
        }, best_score, "fallback", "db"

    llm.setdefault("solution", "")
    return llm, best_score, "llm", "llm"