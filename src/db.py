import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.extensions import connection
from datetime import datetime
from typing import Any, TypedDict
from config import get_settings

settings = get_settings()

DB_CONFIG = {
    'dbname': settings.DB_NAME,
    'user': settings.DB_USER, 
    'password': settings.DB_PASSWORD,
    'host': settings.DB_HOST,
    'port': settings.DB_PORT,
}


def get_db_connection() -> connection:
    return psycopg2.connect(**DB_CONFIG)


def init_db() -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS webhook_messages (
                    id SERIAL PRIMARY KEY,
                    payload JSONB NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        conn.commit()

class MessageDict(TypedDict):
    id: int
    payload: dict[str, Any]
    timestamp: str

def get_messages_from_db() -> list[MessageDict]:
    print(f"getting it")

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute('''
                SELECT id, payload, timestamp 
                FROM webhook_messages 
                ORDER BY timestamp DESC
            ''')
            # messages = [dict(row) for row in cur.fetchall()]
            messages = [
                    {
                        'id': row[0],
                        'payload': row[1],
                        'timestamp': row[2].isoformat()
                    }
                    for row in cur.fetchall()
                ]

    print(f"messages are {messages}")
    return messages

def store_message(payload: dict[str, Any]) -> int:  
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO webhook_messages (payload, timestamp) VALUES (%s, %s) RETURNING id',
                (psycopg2.extras.Json(payload), datetime.utcnow())
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError("Failed to insert message")
            message_id = row[0]
            conn.commit()
    print(f"message_id is {message_id}, payload is {payload}")
    return message_id


def get_n_latest_messages_from_channel(phone: str, group_name: str, n: int) -> list[dict]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute('''
                SELECT payload->'message'->'text' 
                FROM webhook_messages
                WHERE payload->>'from' ILIKE %s AND payload->>'from' ILIKE %s
                        -- filter out rows that are not messages
                        AND payload ->> 'message' IS NOT NULL 
                ORDER BY timestamp DESC
                LIMIT %s
            ''', (f'%{phone}%', f'%{group_name}%', str(n)))

            messages = [
                    
                    row[0]
                    
                    for row in cur.fetchall()
                ]
    return messages