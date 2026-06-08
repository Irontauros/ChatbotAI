import os
import psycopg2
import json
from datetime import datetime, timezone

# Garante encoding correto para PostgreSQL
os.environ["PGCLIENTENCODING"] = "utf8"


# Cria ligação à base de dados
def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="incident_ai",
        user="postgres",
        password="0402"
    )


# Limpa tabela temporária de incidentes
def clear_incidents(conn):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE incidents;")
    conn.commit()


# Insere incidente processado (antes do feedback)
def insert_incident(conn, data):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO incidents (
                id, description, category, urgency, impact, priority,
                solution, confidence, mode, top_k, created_at
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                data["id"],
                data["description"],
                data["prediction"]["category"],
                data["prediction"]["urgency"],
                data["prediction"]["impact"],
                data["prediction"]["priority"],

                # solução já entra como os outros campos
                data["prediction"].get("solution"),

                data["confidence"],
                data["mode"],

                # guarda top_k como JSON
                json.dumps(data["top_k"]),

                # timestamp correto com timezone
                datetime.now(timezone.utc)
            )
        )
    conn.commit()


# Carrega casos já resolvidos (base de conhecimento)
def load_resolved(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT new_id, description, category, urgency, impact, priority, solution, date
            FROM resolved
        """)
        rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "description": r[1],
            "category": r[2],
            "urgency": r[3],
            "impact": r[4],
            "priority": r[5],
            "solution": r[6],
            "date": r[7].isoformat() if r[7] else None
        }
        for r in rows
    ]


# Carrega incidentes temporários (para feedback)
def load_incidents(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, description, category, urgency, impact, priority, solution
            FROM incidents
        """)
        rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "description": r[1],
            "category": r[2],
            "urgency": r[3],
            "impact": r[4],
            "priority": r[5],
            "solution": r[6]
        }
        for r in rows
    ]


# Insere incidente validado pelo utilizador (vai para base final)
def insert_resolved(conn, data):
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO resolved (
                    description, category, urgency, impact, priority, solution, date
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    data["description"],
                    data["category"],
                    data["urgency"],
                    data["impact"],
                    data["priority"],
                    data.get("solution"),

                    # timestamp com timezone correto
                    datetime.now(timezone.utc)
                )
            )
        conn.commit()

    except Exception as e:
        conn.rollback()
        print("DB ERROR:", e)


# Remove incidente após feedback
def delete_incident(conn, incident_id):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM incidents WHERE id = %s", (incident_id,))
    conn.commit()