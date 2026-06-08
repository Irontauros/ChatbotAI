import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:mini"


# Gera o prompt com instruções e contexto opcional
def build_prompt(description, context_tickets=None):

    context_text = ""

    # Contexto com exemplos anteriores
    if context_tickets:
        context_text = "\nSimilar past incidents:\n"

        for i, t in enumerate(context_tickets[:5]):
            ticket = t.get("ticket", {})

            context_text += f"""
Example {i+1}:
Category: {ticket.get("category")}
Urgency: {ticket.get("urgency")}
Impact: {ticket.get("impact")}
Priority: {ticket.get("priority")}
Solution: {ticket.get("solution")}
Description: {ticket.get("description", "N/A")}
"""

    # Prompt final
    return f"""
You are an IT support incident classifier.

When similar incidents are provided, reuse BOTH classification and solution patterns.

{context_text}

Incident:
{description}

Classify the incident and provide a solution when possible.

Category options:
Network
Hardware
Software
Security
Web Service
Email
Printer
VPN

Urgency:
Low
Medium
High

Impact:
Low
Moderate
Critical

Priority:
Low
Medium
High
Critical

Return ONLY JSON.

{{
"category":"",
"urgency":"",
"impact":"",
"priority":"",
"solution":""
}}
"""


# Extrai JSON da resposta do modelo
def extract_json(text):
    match = re.search(r"\{.*?\}", text, re.S)

    if not match:
        return {"error": "No JSON found"}

    json_str = match.group()

    try:
        return json.loads(json_str)
    except:
        return {"error": "Invalid JSON"}


# Classifica incidente com ou sem contexto
def classify_incident(description, context_tickets=None):

    prompt = build_prompt(description, context_tickets)

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0,
                    "num_predict": 120,   # ↑ ligeiramente maior por causa da solution
                    "top_k": 20
                }
            },
            timeout=120
        )

        if response.status_code != 200:
            print("\nHTTP ERROR:", response.status_code)
            return {"error": "HTTP failure"}

        data = response.json()

        if "response" not in data:
            print("\nFULL ERROR RESPONSE FROM OLLAMA:")
            print(data)
            return {"error": "LLM failed"}

        text = data["response"]

        print("\nRAW LLM RESPONSE:")
        print(text)

        result = extract_json(text)

        if "error" in result:
            print("JSON parsing failed:", result["error"])
            return {"error": "Invalid LLM output"}

        # 🔥 GARANTE que solution existe sempre
        result["solution"] = result.get("solution") or None

        return result

    except requests.exceptions.Timeout:
        print("\nTimeout from Ollama")
        return {"error": "Timeout"}

    except Exception as e:
        print("\nUnexpected error:", str(e))
        return {"error": "Unknown failure"}