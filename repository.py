import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")


def save_query_log(input_text, category, urgency, confidence, reason):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO query_logs (input_text, category, urgency, confidence, reason)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (input_text, category, urgency, confidence, reason)
    )

    conn.commit()
    cursor.close()
    conn.close()