import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv(override=True)

DATABASE_NAME = os.getenv("DATABASE_NAME")
PASSWORD = os.getenv("PASSWORD")

"""
This file is responsible for making database queries, which your fastapi endpoints/routes can use.
The reason we split them up is to avoid clutter in the endpoints, so that the endpoints might focus on other tasks 

- Try to return results with cursor.fetchall() or cursor.fetchone() when possible
- Make sure you always give the user response if something went right or wrong, sometimes 
you might need to use the RETURNING keyword to garantuee that something went right / wrong
e.g when making DELETE or UPDATE queries
- No need to use a class here
- Try to raise exceptions to make them more reusable and work a lot with returns
- You will need to decide which parameters each function should receive. All functions 
start with a connection parameter.
- Below, a few inspirational functions exist - feel free to completely ignore how they are structured
- E.g, if you decide to use psycopg3, you'd be able to directly use pydantic models with the cursor, these examples are however using psycopg2 and RealDictCursor
"""


import json

from psycopg2.extras import RealDictCursor

"""
DATABASE FUNCTIONS
------------------
All database operations are here.
Each function takes conn first.
Uses:
- with conn: auto commit/rollback
- RealDictCursor: returns dict rows
- RETURNING: proves insert/update/delete worked
"""

# ============================================
# USERS
# ============================================

def users_list(conn):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, email, avatar_url, role, created_at, updated_at
                FROM users
                ORDER BY id;
            """)
            return cur.fetchall()

def users_get(conn, user_id: int):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, email, avatar_url, role, created_at, updated_at
                FROM users
                WHERE id = %s;
            """, (user_id,))
            return cur.fetchone()

def users_create(conn, email: str, password_hash: str, avatar_url=None, role="teacher"):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO users (email, password_hash, avatar_url, role)
                VALUES (%s, %s, %s, %s)
                RETURNING id, email, avatar_url, role, created_at, updated_at;
            """, (email, password_hash, avatar_url, role))
            return cur.fetchone()

def users_update(conn, user_id: int, email: str, password_hash: str, avatar_url, role: str):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                UPDATE users
                SET email = %s,
                    password_hash = %s,
                    avatar_url = %s,
                    role = %s,
                    updated_at = now()
                WHERE id = %s
                RETURNING id, email, avatar_url, role, created_at, updated_at;
            """, (email, password_hash, avatar_url, role, user_id))
            return cur.fetchone()

def users_patch(conn, user_id: int, email=None, password_hash=None, avatar_url=None, role=None):
    # SAFE PATCH (whitelist)
    updates = []
    values = []

    if email is not None:
        updates.append("email = %s")
        values.append(email)
    if password_hash is not None:
        updates.append("password_hash = %s")
        values.append(password_hash)
    if avatar_url is not None:
        updates.append("avatar_url = %s")
        values.append(avatar_url)
    if role is not None:
        updates.append("role = %s")
        values.append(role)

    if not updates:
        return None

    values.append(user_id)

    sql = f"""
        UPDATE users
        SET {", ".join(updates)}, updated_at = now()
        WHERE id = %s
        RETURNING id, email, avatar_url, role, created_at, updated_at;
    """

    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, values)
            return cur.fetchone()

def users_delete(conn, user_id: int) -> bool:
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM users WHERE id = %s RETURNING id;", (user_id,))
            return cur.fetchone() is not None


# ============================================
# PRESENTATIONS
# ============================================

def presentations_list(conn):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT p.id, p.owner_id, p.title, p.created_at, p.updated_at,
                       u.email AS owner_email
                FROM presentations p
                JOIN users u ON u.id = p.owner_id
                ORDER BY p.created_at DESC;
            """)
            return cur.fetchall()

def presentations_get(conn, presentation_id: int):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT p.id, p.owner_id, p.title, p.created_at, p.updated_at,
                       u.email AS owner_email
                FROM presentations p
                JOIN users u ON u.id = p.owner_id
                WHERE p.id = %s;
            """, (presentation_id,))
            return cur.fetchone()

def presentations_create(conn, owner_id: int, title: str):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO presentations (owner_id, title)
                VALUES (%s, %s)
                RETURNING id, owner_id, title, created_at, updated_at;
            """, (owner_id, title))
            return cur.fetchone()

def presentations_update(conn, presentation_id: int, owner_id: int, title: str):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                UPDATE presentations
                SET owner_id = %s,
                    title = %s,
                    updated_at = now()
                WHERE id = %s
                RETURNING id, owner_id, title, created_at, updated_at;
            """, (owner_id, title, presentation_id))
            return cur.fetchone()

def presentations_delete(conn, presentation_id: int) -> bool:
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM presentations WHERE id = %s RETURNING id;", (presentation_id,))
            return cur.fetchone() is not None


# ============================================
# QUESTION TYPES
# ============================================

def question_types_list(conn):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT code, label, uses_options, allows_text_answer
                FROM question_types
                ORDER BY code;
            """)
            return cur.fetchall()


# ============================================
# QUESTIONS
# ============================================

def questions_list_for_presentation(conn, presentation_id: int):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT q.id, q.presentation_id, q.type_code, q.text, q.media_url,
                       q.order_index, q.settings, q.created_at, q.updated_at,
                       qt.label AS type_label
                FROM questions q
                JOIN question_types qt ON qt.code = q.type_code
                WHERE q.presentation_id = %s
                ORDER BY q.order_index, q.id;
            """, (presentation_id,))
            return cur.fetchall()

def questions_get(conn, question_id: int):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT q.id, q.presentation_id, q.type_code, q.text, q.media_url,
                       q.order_index, q.settings, q.created_at, q.updated_at,
                       qt.label AS type_label
                FROM questions q
                JOIN question_types qt ON qt.code = q.type_code
                WHERE q.id = %s;
            """, (question_id,))
            return cur.fetchone()

def questions_create(conn, presentation_id: int, type_code: str, text: str,
                    media_url=None, order_index=0, settings=None):
    settings_json = json.dumps(settings or {})
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO questions (presentation_id, type_code, text, media_url, order_index, settings)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                RETURNING id, presentation_id, type_code, text, media_url, order_index, settings, created_at, updated_at;
            """, (presentation_id, type_code, text, media_url, order_index, settings_json))
            return cur.fetchone()

def questions_update(conn, question_id: int, presentation_id: int, type_code: str, text: str,
                    media_url, order_index: int, settings):
    settings_json = json.dumps(settings or {})
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                UPDATE questions
                SET presentation_id = %s,
                    type_code = %s,
                    text = %s,
                    media_url = %s,
                    order_index = %s,
                    settings = %s::jsonb,
                    updated_at = now()
                WHERE id = %s
                RETURNING id, presentation_id, type_code, text, media_url, order_index, settings, created_at, updated_at;
            """, (presentation_id, type_code, text, media_url, order_index, settings_json, question_id))
            return cur.fetchone()

def questions_delete(conn, question_id: int) -> bool:
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM questions WHERE id = %s RETURNING id;", (question_id,))
            return cur.fetchone() is not None


# ============================================
# OPTIONS
# ============================================

def options_list_for_question(conn, question_id: int):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, question_id, text, is_correct, order_index
                FROM options
                WHERE question_id = %s
                ORDER BY order_index, id;
            """, (question_id,))
            return cur.fetchall()

def options_create(conn, question_id: int, text: str, is_correct=False, order_index=0):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO options (question_id, text, is_correct, order_index)
                VALUES (%s, %s, %s, %s)
                RETURNING id, question_id, text, is_correct, order_index;
            """, (question_id, text, is_correct, order_index))
            return cur.fetchone()

def options_update(conn, option_id: int, question_id: int, text: str, is_correct: bool, order_index: int):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                UPDATE options
                SET question_id = %s,
                    text = %s,
                    is_correct = %s,
                    order_index = %s
                WHERE id = %s
                RETURNING id, question_id, text, is_correct, order_index;
            """, (question_id, text, is_correct, order_index, option_id))
            return cur.fetchone()

def options_delete(conn, option_id: int) -> bool:
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM options WHERE id = %s RETURNING id;", (option_id,))
            return cur.fetchone() is not None


# ============================================
# LIVE SESSIONS
# ============================================

def sessions_list(conn):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT ls.id, ls.presentation_id, ls.access_code, ls.status,
                       ls.current_question_id, ls.created_at, ls.started_at, ls.ended_at,
                       p.title AS presentation_title
                FROM live_sessions ls
                JOIN presentations p ON p.id = ls.presentation_id
                ORDER BY ls.created_at DESC;
            """)
            return cur.fetchall()

def sessions_get(conn, session_id: int):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, presentation_id, access_code, status, current_question_id,
                       created_at, started_at, ended_at
                FROM live_sessions
                WHERE id = %s;
            """, (session_id,))
            return cur.fetchone()

def sessions_get_by_code(conn, access_code: str):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, presentation_id, access_code, status, current_question_id,
                       created_at, started_at, ended_at
                FROM live_sessions
                WHERE access_code = %s;
            """, (access_code,))
            return cur.fetchone()

def sessions_create(conn, presentation_id: int, access_code: str, status="created", current_question_id=None):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO live_sessions (presentation_id, access_code, status, current_question_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id, presentation_id, access_code, status, current_question_id, created_at, started_at, ended_at;
            """, (presentation_id, access_code, status, current_question_id))
            return cur.fetchone()

def sessions_update(conn, session_id: int, presentation_id: int, access_code: str, status: str, current_question_id=None):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                UPDATE live_sessions
                SET presentation_id = %s,
                    access_code = %s,
                    status = %s,
                    current_question_id = %s
                WHERE id = %s
                RETURNING id, presentation_id, access_code, status, current_question_id, created_at, started_at, ended_at;
            """, (presentation_id, access_code, status, current_question_id, session_id))
            return cur.fetchone()

def sessions_patch(conn, session_id: int, status=None, current_question_id=None):
    updates = []
    values = []

    if status is not None:
        updates.append("status = %s")
        values.append(status)
    if current_question_id is not None:
        updates.append("current_question_id = %s")
        values.append(current_question_id)

    if not updates:
        return None

    values.append(session_id)

    sql = f"""
        UPDATE live_sessions
        SET {", ".join(updates)}
        WHERE id = %s
        RETURNING id, presentation_id, access_code, status, current_question_id, created_at, started_at, ended_at;
    """

    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, values)
            return cur.fetchone()

def sessions_delete(conn, session_id: int) -> bool:
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM live_sessions WHERE id = %s RETURNING id;", (session_id,))
            return cur.fetchone() is not None


# ============================================
# PARTICIPANTS
# ============================================

def participants_list_for_session(conn, session_id: int):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, session_id, nickname, joined_at
                FROM participants
                WHERE session_id = %s
                ORDER BY joined_at, id;
            """, (session_id,))
            return cur.fetchall()

def participants_create(conn, session_id: int, nickname: str):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO participants (session_id, nickname)
                VALUES (%s, %s)
                RETURNING id, session_id, nickname, joined_at;
            """, (session_id, nickname))
            return cur.fetchone()

def participants_delete(conn, participant_id: int) -> bool:
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM participants WHERE id = %s RETURNING id;", (participant_id,))
            return cur.fetchone() is not None


# ============================================
# VOTES
# ============================================

def votes_list_for_session(conn, session_id: int):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT v.id, v.session_id, v.participant_id, v.question_id, v.option_id, v.text_answer, v.created_at,
                       p.nickname,
                       q.text AS question_text
                FROM votes v
                JOIN participants p ON p.id = v.participant_id
                JOIN questions q ON q.id = v.question_id
                WHERE v.session_id = %s
                ORDER BY v.created_at, v.id;
            """, (session_id,))
            return cur.fetchall()

def votes_list_for_question(conn, session_id: int, question_id: int):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT v.id, v.session_id, v.participant_id, v.question_id, v.option_id, v.text_answer, v.created_at,
                       p.nickname
                FROM votes v
                JOIN participants p ON p.id = v.participant_id
                WHERE v.session_id = %s AND v.question_id = %s
                ORDER BY v.created_at, v.id;
            """, (session_id, question_id))
            return cur.fetchall()

def votes_create(conn, session_id: int, participant_id: int, question_id: int, option_id=None, text_answer=None):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO votes (session_id, participant_id, question_id, option_id, text_answer)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, session_id, participant_id, question_id, option_id, text_answer, created_at;
            """, (session_id, participant_id, question_id, option_id, text_answer))
            return cur.fetchone()


# ============================================
# Q&A MESSAGES
# ============================================

def qna_messages_list_for_session(conn, session_id: int):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT m.id, m.session_id, m.participant_id, m.text, m.is_answered, m.is_hidden, m.created_at,
                       p.nickname,
                       (SELECT COUNT(*) FROM qna_upvotes u WHERE u.message_id = m.id) AS upvote_count
                FROM qna_messages m
                LEFT JOIN participants p ON p.id = m.participant_id
                WHERE m.session_id = %s
                ORDER BY m.created_at DESC, m.id DESC;
            """, (session_id,))
            return cur.fetchall()

def qna_messages_create(conn, session_id: int, text: str, participant_id=None):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO qna_messages (session_id, participant_id, text)
                VALUES (%s, %s, %s)
                RETURNING id, session_id, participant_id, text, is_answered, is_hidden, created_at;
            """, (session_id, participant_id, text))
            return cur.fetchone()

def qna_messages_patch(conn, message_id: int, is_answered=None, is_hidden=None):
    updates = []
    values = []

    if is_answered is not None:
        updates.append("is_answered = %s")
        values.append(is_answered)
    if is_hidden is not None:
        updates.append("is_hidden = %s")
        values.append(is_hidden)

    if not updates:
        return None

    values.append(message_id)

    sql = f"""
        UPDATE qna_messages
        SET {", ".join(updates)}
        WHERE id = %s
        RETURNING id, session_id, participant_id, text, is_answered, is_hidden, created_at;
    """

    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, values)
            return cur.fetchone()

def qna_messages_delete(conn, message_id: int) -> bool:
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM qna_messages WHERE id = %s RETURNING id;", (message_id,))
            return cur.fetchone() is not None


# ============================================
# Q&A UPVOTES
# ============================================

def qna_upvotes_create(conn, message_id: int, participant_id: int):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO qna_upvotes (message_id, participant_id)
                VALUES (%s, %s)
                RETURNING id, message_id, participant_id, created_at;
            """, (message_id, participant_id))
            return cur.fetchone()

def qna_upvotes_delete(conn, message_id: int, participant_id: int) -> bool:
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                DELETE FROM qna_upvotes
                WHERE message_id = %s AND participant_id = %s
                RETURNING id;
            """, (message_id, participant_id))
            return cur.fetchone() is not None
