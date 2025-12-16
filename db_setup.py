import os

import psycopg2
from dotenv import load_dotenv

load_dotenv(override=True)

DATABASE_NAME = os.getenv("DATABASE_NAME")
PASSWORD = os.getenv("PASSWORD")


def get_connection():
    """
    Function that returns a single connection
    In reality, we might use a connection pool, since
    this way we'll start a new connection each time
    someone hits one of our endpoints, which isn't great for performance
    """
    return psycopg2.connect(
        dbname=DATABASE_NAME,
        user="postgres",  # change if needed
        password=PASSWORD,
        host="localhost",  # change if needed
        port="5432",  # change if needed
    )


def create_tables():
    con = get_connection()
    cur = con.cursor()

    try:
        # ----------------------------
        # USERS
        # ----------------------------
        cur.execute("""
        CREATE TABLE users (
            id            SERIAL PRIMARY KEY,
            email         VARCHAR(255) NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            avatar_url    TEXT NULL,
            role          VARCHAR(30) NOT NULL DEFAULT 'teacher',
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """)

        # ----------------------------
        # PRESENTATIONS
        # ----------------------------
        cur.execute("""
        CREATE TABLE presentations (
            id         SERIAL PRIMARY KEY,
            owner_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title      VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """)

        # ----------------------------
        # QUESTION TYPES (lookup)
        # ----------------------------
        cur.execute("""
        CREATE TABLE question_types (
            code               VARCHAR(50) PRIMARY KEY,
            label              VARCHAR(100) NOT NULL,
            uses_options        BOOLEAN NOT NULL DEFAULT FALSE,
            allows_text_answer  BOOLEAN NOT NULL DEFAULT FALSE
        );
        """)

        # Seed 
        cur.execute("""
        INSERT INTO question_types (code, label, uses_options, allows_text_answer) VALUES
        ('multiple_choice','Multiple choice', TRUE,  FALSE),
        ('quiz','Quiz', TRUE, FALSE),
        ('open_ended','Open ended', FALSE, TRUE),
        ('word_cloud','Word cloud', FALSE, TRUE),
        ('scales','Scales', FALSE, FALSE),
        ('ranking','Ranking', FALSE, FALSE),
        ('qna','Q&A', FALSE, TRUE),
        ('image_choice','Image choice', TRUE, FALSE),
        ('slider','Slider', FALSE, FALSE),
        ('grid','Grid', FALSE, FALSE),
        ('prioritization','Prioritization', FALSE, FALSE),
        ('quick_form','Quick form', FALSE, TRUE),
        ('content_slide','Content slide', FALSE, FALSE)
        ON CONFLICT (code) DO NOTHING;
        """)

        # ----------------------------
        # QUESTIONS
        # ----------------------------
        cur.execute("""
        CREATE TABLE questions (
            id              SERIAL PRIMARY KEY,
            presentation_id INT NOT NULL REFERENCES presentations(id) ON DELETE CASCADE,
            type_code       VARCHAR(50) NOT NULL REFERENCES question_types(code),
            text            TEXT NOT NULL,
            media_url       TEXT NULL,
            order_index     INTEGER NOT NULL DEFAULT 0,
            settings        JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """)

        # ----------------------------
        # OPTIONS
        # ----------------------------
        cur.execute("""
        CREATE TABLE options (
            id          SERIAL PRIMARY KEY,
            question_id INT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
            text        TEXT NOT NULL,
            is_correct  BOOLEAN NOT NULL DEFAULT FALSE,
            order_index INT NOT NULL DEFAULT 0
        );
        """)

        # ----------------------------
        # LIVE SESSIONS
        # ----------------------------
        cur.execute("""
        CREATE TABLE live_sessions (
            id                  BIGSERIAL PRIMARY KEY,
            presentation_id     BIGINT NOT NULL REFERENCES presentations(id) ON DELETE CASCADE,
            access_code         VARCHAR(12) NOT NULL UNIQUE,
            status              VARCHAR(20) NOT NULL DEFAULT 'created',
            current_question_id INT NULL REFERENCES questions(id) ON DELETE SET NULL,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
            started_at          TIMESTAMPTZ NULL,
            ended_at            TIMESTAMPTZ NULL,
            CONSTRAINT live_sessions_status_check CHECK (status IN ('created','live','ended'))
        );
        """)

        # ----------------------------
        # PARTICIPANTS
        # ----------------------------
        cur.execute("""
        CREATE TABLE participants (
            id         SERIAL PRIMARY KEY,
            session_id INT NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
            nickname   VARCHAR(60) NOT NULL,
            joined_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (session_id, nickname)
        );
        """)

        # ----------------------------
        # VOTES
        # ----------------------------
        cur.execute("""
        CREATE TABLE votes (
            id             SERIAL PRIMARY KEY,
            session_id     INT NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
            participant_id INT NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
            question_id    INT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
            option_id      INT NULL REFERENCES options(id) ON DELETE SET NULL,
            text_answer    TEXT NULL,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),

            CONSTRAINT votes_one_answer_only CHECK (
                (option_id IS NOT NULL) <> (text_answer IS NOT NULL)
            ),
            CONSTRAINT votes_one_per_question UNIQUE (session_id, participant_id, question_id)
        );
        """)

        # ----------------------------
        # Q&A MESSAGES
        # ----------------------------
        cur.execute("""
        CREATE TABLE qna_messages (
            id             SERIAL PRIMARY KEY,
            session_id     INT NOT NULL REFERENCES live_sessions(id) ON DELETE CASCADE,
            participant_id INT NULL REFERENCES participants(id) ON DELETE SET NULL,
            text           TEXT NOT NULL,
            is_answered    BOOLEAN NOT NULL DEFAULT FALSE,
            is_hidden      BOOLEAN NOT NULL DEFAULT FALSE,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """)

        # ----------------------------
        # Q&A UPVOTES (bridge)
        # ----------------------------
        cur.execute("""
        CREATE TABLE qna_upvotes (
            id             SERIAL PRIMARY KEY,
            message_id     INT NOT NULL REFERENCES qna_messages(id) ON DELETE CASCADE,
            participant_id INT NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (message_id, participant_id)
        );
        """)

        # ----------------------------
        # Indexes (performance)
        # ----------------------------
        cur.execute("CREATE INDEX idx_questions_presentation_order ON questions(presentation_id, order_index);")
        cur.execute("CREATE INDEX idx_options_question ON options(question_id);")
        cur.execute("CREATE INDEX idx_sessions_presentation ON live_sessions(presentation_id);")
        cur.execute("CREATE INDEX idx_participants_session ON participants(session_id);")
        cur.execute("CREATE INDEX idx_votes_session_question ON votes(session_id, question_id);")
        cur.execute("CREATE INDEX idx_qna_messages_session ON qna_messages(session_id, created_at);")
        cur.execute("CREATE INDEX idx_qna_upvotes_message ON qna_upvotes(message_id);")

        con.commit()
        print(" Tables created successfully.")

    except Exception as e:
        con.rollback()
        print(" Error creating tables:", e)
        raise

    finally:
        cur.close()
        con.close()

if __name__ == "__main__":
    # Only reason to execute this file would be to create new tables, meaning it serves a migration file
    create_tables()
    print("Tables created successfully.")