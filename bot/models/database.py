import json
import logging
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import aiosqlite
import asyncpg

logger = logging.getLogger(__name__)

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    level TEXT DEFAULT 'Pre-A1',
    goal TEXT,
    selected_language TEXT NOT NULL DEFAULT 'english',
    daily_goal_minutes INTEGER DEFAULT 15,
    reminder_time TEXT,
    streak_days INTEGER DEFAULT 0,
    last_active DATE,
    onboarding_completed INTEGER DEFAULT 0,
    writing_level INTEGER DEFAULT 1,
    grammar_topic_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    language TEXT NOT NULL DEFAULT 'english',
    word TEXT,
    translation TEXT,
    transcription TEXT,
    theme TEXT,
    example_en TEXT,
    example_ru TEXT,
    ease_factor REAL DEFAULT 2.5,
    interval_days INTEGER DEFAULT 1,
    repetitions INTEGER DEFAULT 0,
    next_review DATE,
    learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    language TEXT NOT NULL DEFAULT 'english',
    module TEXT,
    lesson_id TEXT,
    completed INTEGER DEFAULT 0,
    score REAL,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS exam_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    language TEXT NOT NULL DEFAULT 'english',
    source_level TEXT,
    target_level TEXT,
    score INTEGER,
    total INTEGER,
    percentage REAL,
    passed INTEGER DEFAULT 0,
    section_scores TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS tutor_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    language TEXT NOT NULL DEFAULT 'english',
    role TEXT,
    content TEXT,
    intent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE INDEX IF NOT EXISTS idx_tutor_messages_user_created
ON tutor_messages(user_id, created_at);

CREATE TABLE IF NOT EXISTS reminder_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    reminder_type TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE INDEX IF NOT EXISTS idx_reminder_events_user_type
ON reminder_events(user_id, reminder_type, sent_at);

CREATE TABLE IF NOT EXISTS release_views (
    user_id INTEGER,
    release_id TEXT,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, release_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS dialogues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    language TEXT NOT NULL DEFAULT 'english',
    scenario TEXT,
    messages TEXT,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    achievement_code TEXT,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, achievement_code),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS exercise_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT UNIQUE,
    payload TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    level TEXT DEFAULT 'Pre-A1',
    goal TEXT,
    selected_language TEXT NOT NULL DEFAULT 'english',
    daily_goal_minutes INTEGER DEFAULT 15,
    reminder_time TEXT,
    streak_days INTEGER DEFAULT 0,
    last_active DATE,
    onboarding_completed INTEGER DEFAULT 0,
    writing_level INTEGER DEFAULT 1,
    grammar_topic_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_words (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    language TEXT NOT NULL DEFAULT 'english',
    word TEXT,
    translation TEXT,
    transcription TEXT,
    theme TEXT,
    example_en TEXT,
    example_ru TEXT,
    ease_factor DOUBLE PRECISION DEFAULT 2.5,
    interval_days INTEGER DEFAULT 1,
    repetitions INTEGER DEFAULT 0,
    next_review DATE,
    learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS progress (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    language TEXT NOT NULL DEFAULT 'english',
    module TEXT,
    lesson_id TEXT,
    completed INTEGER DEFAULT 0,
    score DOUBLE PRECISION,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS exam_attempts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    language TEXT NOT NULL DEFAULT 'english',
    source_level TEXT,
    target_level TEXT,
    score INTEGER,
    total INTEGER,
    percentage DOUBLE PRECISION,
    passed INTEGER DEFAULT 0,
    section_scores TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS tutor_messages (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    language TEXT NOT NULL DEFAULT 'english',
    role TEXT,
    content TEXT,
    intent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE INDEX IF NOT EXISTS idx_tutor_messages_user_created
ON tutor_messages(user_id, created_at);

CREATE TABLE IF NOT EXISTS reminder_events (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    reminder_type TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE INDEX IF NOT EXISTS idx_reminder_events_user_type
ON reminder_events(user_id, reminder_type, sent_at);

CREATE TABLE IF NOT EXISTS release_views (
    user_id BIGINT,
    release_id TEXT,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, release_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS dialogues (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    language TEXT NOT NULL DEFAULT 'english',
    scenario TEXT,
    messages TEXT,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS achievements (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    achievement_code TEXT,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, achievement_code),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS exercise_cache (
    id BIGSERIAL PRIMARY KEY,
    cache_key TEXT UNIQUE,
    payload TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _asyncpg_url(database_url: str) -> str:
    """Remove libpq-only options that asyncpg does not accept."""
    parsed = urlsplit(database_url)
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key != "channel_binding"
    ]
    return urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment)
    )


def _postgres_query(query: str) -> str:
    """Translate sqlite-style placeholders to asyncpg placeholders."""
    parts = query.split("?")
    if len(parts) == 1:
        return query
    translated = [parts[0]]
    for index, part in enumerate(parts[1:], start=1):
        translated.extend((f"${index}", part))
    return "".join(translated)


class Database:
    def __init__(self, db_path: Path, database_url: str | None = None) -> None:
        self.db_path = db_path
        self.database_url = database_url
        self._sqlite: aiosqlite.Connection | None = None
        self._postgres: asyncpg.Pool | None = None

    @property
    def is_postgres(self) -> bool:
        return bool(
            self.database_url
            and self.database_url.startswith(("postgres://", "postgresql://"))
        )

    async def connect(self) -> None:
        if self.is_postgres:
            self._postgres = await asyncpg.create_pool(
                dsn=_asyncpg_url(self.database_url or ""),
                min_size=1,
                max_size=5,
                command_timeout=30,
            )
            async with self._postgres.acquire() as connection:
                await connection.execute(POSTGRES_SCHEMA)
            await self._run_language_migrations()
            logger.info("PostgreSQL database initialized")
            return

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._sqlite = await aiosqlite.connect(self.db_path)
        self._sqlite.row_factory = aiosqlite.Row
        await self._sqlite.executescript(SQLITE_SCHEMA)
        await self._sqlite.commit()
        await self._run_language_migrations()
        logger.info("Database initialized at %s", self.db_path)

    async def _run_language_migrations(self) -> None:
        language_columns = {
            "users": ("selected_language", "TEXT NOT NULL DEFAULT 'english'"),
            "user_words": ("language", "TEXT NOT NULL DEFAULT 'english'"),
            "progress": ("language", "TEXT NOT NULL DEFAULT 'english'"),
            "exam_attempts": ("language", "TEXT NOT NULL DEFAULT 'english'"),
            "tutor_messages": ("language", "TEXT NOT NULL DEFAULT 'english'"),
            "dialogues": ("language", "TEXT NOT NULL DEFAULT 'english'"),
        }
        if self.is_postgres:
            for table, (column, definition) in language_columns.items():
                await self.execute(
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS "
                    f"{column} {definition}"
                )
        else:
            for table, (column, definition) in language_columns.items():
                columns = await self.fetchall(f"PRAGMA table_info({table})")
                if column not in {str(row["name"]) for row in columns}:
                    await self.execute(
                        f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
                    )

        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_profiles (
                user_id BIGINT NOT NULL,
                language TEXT NOT NULL,
                level TEXT DEFAULT 'Pre-A1',
                writing_level INTEGER DEFAULT 1,
                grammar_topic_index INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, language),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """
        )
        await self.execute(
            """
            INSERT INTO learning_profiles (
                user_id, language, level, writing_level, grammar_topic_index
            )
            SELECT user_id, 'english', level, writing_level, grammar_topic_index
            FROM users
            WHERE 1 = 1
            ON CONFLICT(user_id, language) DO NOTHING
            """
        )
        await self.execute("DROP INDEX IF EXISTS idx_user_words_user_word")
        await self.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_user_words_user_language_word
            ON user_words(user_id, language, word)
            """
        )

    async def close(self) -> None:
        if self._postgres:
            await self._postgres.close()
            self._postgres = None
        if self._sqlite:
            await self._sqlite.close()
            self._sqlite = None

    def _sqlite_connection(self) -> aiosqlite.Connection:
        if not self._sqlite:
            raise RuntimeError("SQLite database is not connected")
        return self._sqlite

    def _postgres_pool(self) -> asyncpg.Pool:
        if not self._postgres:
            raise RuntimeError("PostgreSQL database is not connected")
        return self._postgres

    async def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        if self.is_postgres:
            await self._postgres_pool().execute(_postgres_query(query), *params)
            return
        connection = self._sqlite_connection()
        await connection.execute(query, params)
        await connection.commit()

    async def fetchone(
        self, query: str, params: tuple[Any, ...] = ()
    ) -> Any | None:
        if self.is_postgres:
            return await self._postgres_pool().fetchrow(
                _postgres_query(query), *params
            )
        cursor = await self._sqlite_connection().execute(query, params)
        return await cursor.fetchone()

    async def fetchall(
        self, query: str, params: tuple[Any, ...] = ()
    ) -> list[Any]:
        if self.is_postgres:
            return list(
                await self._postgres_pool().fetch(_postgres_query(query), *params)
            )
        cursor = await self._sqlite_connection().execute(query, params)
        return await cursor.fetchall()

    async def get_or_create_user(self, user_id: int, username: str | None = None) -> dict[str, Any]:
        row = await self.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not row:
            await self.execute(
                """
                INSERT INTO users (user_id, username, last_active)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO NOTHING
                """,
                (user_id, username, date.today()),
            )
            row = await self.fetchone(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,),
            )
        if not row:
            return {}
        user = dict(row)
        language = str(user.get("selected_language") or "english")
        profile = await self.get_learning_profile(user_id, language)
        user.update(profile)
        user["learning_language"] = language
        return user

    async def update_user(self, user_id: int, **fields: Any) -> None:
        if not fields:
            return
        learning_fields = {
            key: fields.pop(key)
            for key in ("level", "writing_level", "grammar_topic_index")
            if key in fields
        }
        if fields:
            columns = ", ".join(f"{key} = ?" for key in fields)
            values = tuple(fields.values()) + (user_id,)
            await self.execute(
                f"UPDATE users SET {columns} WHERE user_id = ?",
                values,
            )
        if learning_fields:
            await self.update_learning_profile(user_id, **learning_fields)
        if "selected_language" in fields:
            await self.get_learning_profile(
                user_id,
                str(fields["selected_language"]),
            )

    async def get_learning_language(self, user_id: int) -> str:
        row = await self.fetchone(
            "SELECT selected_language FROM users WHERE user_id = ?",
            (user_id,),
        )
        return str(row["selected_language"] or "english") if row else "english"

    async def get_learning_profile(
        self,
        user_id: int,
        language: str | None = None,
    ) -> dict[str, Any]:
        language = language or await self.get_learning_language(user_id)
        await self.execute(
            """
            INSERT INTO learning_profiles (user_id, language)
            VALUES (?, ?)
            ON CONFLICT(user_id, language) DO NOTHING
            """,
            (user_id, language),
        )
        row = await self.fetchone(
            """
            SELECT level, writing_level, grammar_topic_index
            FROM learning_profiles
            WHERE user_id = ? AND language = ?
            """,
            (user_id, language),
        )
        return dict(row) if row else {
            "level": "Pre-A1",
            "writing_level": 1,
            "grammar_topic_index": 0,
        }

    async def update_learning_profile(
        self,
        user_id: int,
        language: str | None = None,
        **fields: Any,
    ) -> None:
        allowed = {"level", "writing_level", "grammar_topic_index"}
        values_to_update = {
            key: value for key, value in fields.items() if key in allowed
        }
        if not values_to_update:
            return
        language = language or await self.get_learning_language(user_id)
        await self.get_learning_profile(user_id, language)
        columns = ", ".join(f"{key} = ?" for key in values_to_update)
        values = tuple(values_to_update.values()) + (user_id, language)
        await self.execute(
            f"UPDATE learning_profiles SET {columns} "
            "WHERE user_id = ? AND language = ?",
            values,
        )

    async def set_learning_language(self, user_id: int, language: str) -> None:
        if language not in {"english", "italian"}:
            raise ValueError(f"Unsupported learning language: {language}")
        await self.get_or_create_user(user_id)
        await self.execute(
            "UPDATE users SET selected_language = ? WHERE user_id = ?",
            (language, user_id),
        )
        await self.get_learning_profile(user_id, language)

    async def touch_activity(self, user_id: int) -> int:
        user = await self.get_or_create_user(user_id)
        today = date.today()
        last_active = user.get("last_active")
        streak = int(user.get("streak_days") or 0)

        if last_active:
            last_date = (
                last_active
                if isinstance(last_active, date)
                else date.fromisoformat(last_active)
            )
            delta = (today - last_date).days
            if delta == 1:
                streak += 1
            elif delta > 1:
                streak = 1
            elif delta == 0:
                streak = max(1, streak)
        else:
            streak = 1

        await self.update_user(user_id, streak_days=streak, last_active=today)
        return streak

    async def add_progress(
        self,
        user_id: int,
        module: str,
        lesson_id: str,
        score: float | None = None,
        completed: bool = True,
        language: str | None = None,
    ) -> None:
        language = language or await self.get_learning_language(user_id)
        await self.execute(
            """
            INSERT INTO progress (
                user_id, language, module, lesson_id, completed, score, completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                language,
                module,
                lesson_id,
                int(completed),
                score,
                datetime.now(UTC).replace(tzinfo=None),
            ),
        )

    async def get_stats(self, user_id: int) -> dict[str, Any]:
        user = await self.get_or_create_user(user_id)
        language = str(user.get("learning_language") or "english")
        words_row = await self.fetchone(
            """
            SELECT
                COUNT(*) AS introduced,
                COALESCE(SUM(CASE WHEN repetitions < 3 THEN 1 ELSE 0 END), 0) AS learning,
                COALESCE(SUM(CASE WHEN repetitions >= 3 THEN 1 ELSE 0 END), 0) AS mastered
            FROM user_words
            WHERE user_id = ? AND language = ?
            """,
            (user_id, language),
        )
        due_row = await self.fetchone(
            """
            SELECT COUNT(*) AS cnt
            FROM user_words
            WHERE user_id = ? AND language = ?
              AND (next_review IS NULL OR next_review <= ?)
            """,
            (user_id, language, date.today()),
        )
        lessons_row = await self.fetchone(
            """
            SELECT COUNT(*) AS cnt FROM progress
            WHERE user_id = ? AND language = ? AND completed = 1
            """,
            (user_id, language),
        )
        accuracy_row = await self.fetchone(
            """
            SELECT AVG(score) AS avg_score
            FROM progress
            WHERE user_id = ?
              AND language = ?
              AND score IS NOT NULL
              AND module IN ('reading', 'grammar', 'writing', 'listening', 'dialogue')
            """,
            (user_id, language),
        )
        achievements = await self.fetchall(
            "SELECT achievement_code, unlocked_at FROM achievements WHERE user_id = ? ORDER BY unlocked_at",
            (user_id,),
        )
        return {
            "level": user.get("level", "Pre-A1"),
            "learning_language": language,
            "goal": user.get("goal"),
            "streak_days": user.get("streak_days", 0),
            "words_introduced": int(words_row["introduced"] or 0) if words_row else 0,
            "words_learning": int(words_row["learning"] or 0) if words_row else 0,
            "words_mastered": int(words_row["mastered"] or 0) if words_row else 0,
            "words_due": int(due_row["cnt"] or 0) if due_row else 0,
            # Backwards-compatible name used by summaries; now means actual mastery.
            "words_learned": int(words_row["mastered"] or 0) if words_row else 0,
            "lessons_completed": lessons_row["cnt"] if lessons_row else 0,
            "accuracy": round(accuracy_row["avg_score"] or 0, 1) if accuracy_row else 0,
            "achievements": [dict(a) for a in achievements],
        }

    async def unlock_achievement(self, user_id: int, code: str) -> bool:
        existing = await self.fetchone(
            "SELECT id FROM achievements WHERE user_id = ? AND achievement_code = ?",
            (user_id, code),
        )
        if existing:
            return False
        await self.execute(
            "INSERT INTO achievements (user_id, achievement_code) VALUES (?, ?)",
            (user_id, code),
        )
        return True

    async def record_exam_attempt(
        self,
        user_id: int,
        source_level: str,
        target_level: str,
        score: int,
        total: int,
        percentage: float,
        passed: bool,
        section_scores: dict[str, dict[str, int]],
        language: str | None = None,
    ) -> None:
        language = language or await self.get_learning_language(user_id)
        await self.execute(
            """
            INSERT INTO exam_attempts (
                user_id, language, source_level, target_level, score, total,
                percentage, passed, section_scores
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                language,
                source_level,
                target_level,
                score,
                total,
                percentage,
                int(passed),
                json.dumps(section_scores, ensure_ascii=False),
            ),
        )

    async def get_latest_exam_attempt(
        self,
        user_id: int,
        target_level: str,
    ) -> dict[str, Any] | None:
        language = await self.get_learning_language(user_id)
        row = await self.fetchone(
            """
            SELECT * FROM exam_attempts
            WHERE user_id = ? AND language = ? AND target_level = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (user_id, language, target_level),
        )
        if not row:
            return None
        result = dict(row)
        result["section_scores"] = json.loads(result.get("section_scores") or "{}")
        return result

    async def get_lesson_attempt_count(self, user_id: int, module: str) -> int:
        language = await self.get_learning_language(user_id)
        row = await self.fetchone(
            """
            SELECT COUNT(*) AS cnt FROM progress
            WHERE user_id = ? AND language = ? AND module = ? AND completed = 1
            """,
            (user_id, language, module),
        )
        return int(row["cnt"]) if row else 0

    async def add_tutor_message(
        self,
        user_id: int,
        role: str,
        content: str,
        intent: str | None = None,
    ) -> None:
        language = await self.get_learning_language(user_id)
        await self.execute(
            """
            INSERT INTO tutor_messages (user_id, language, role, content, intent)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, language, role, content, intent),
        )

    async def get_recent_tutor_messages(
        self,
        user_id: int,
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        language = await self.get_learning_language(user_id)
        rows = await self.fetchall(
            """
            SELECT role, content, intent, created_at
            FROM tutor_messages
            WHERE user_id = ? AND language = ?
              AND (intent IS NULL OR intent <> 'next')
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, language, limit),
        )
        return [dict(row) for row in reversed(rows)]

    async def clear_ai_history(self, user_id: int) -> None:
        language = await self.get_learning_language(user_id)
        await self.execute(
            "DELETE FROM tutor_messages WHERE user_id = ? AND language = ?",
            (user_id, language),
        )
        await self.execute(
            "DELETE FROM dialogues WHERE user_id = ? AND language = ?",
            (user_id, language),
        )

    async def get_weak_topics(
        self,
        user_id: int,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        language = await self.get_learning_language(user_id)
        rows = await self.fetchall(
            """
            SELECT p.module, p.lesson_id, p.score AS avg_score, 1 AS attempts
            FROM progress AS p
            WHERE p.user_id = ? AND p.language = ?
              AND p.completed = 1
              AND p.score < 75
              AND p.module IN ('reading', 'grammar', 'writing', 'listening', 'dialogue')
              AND p.id = (
                  SELECT p2.id
                  FROM progress AS p2
                  WHERE p2.user_id = p.user_id
                    AND p2.language = p.language
                    AND p2.module = p.module
                    AND p2.lesson_id = p.lesson_id
                    AND p2.completed = 1
                  ORDER BY p2.completed_at DESC, p2.id DESC
                  LIMIT 1
              )
            ORDER BY p.score ASC, p.completed_at DESC
            LIMIT ?
            """,
            (user_id, language, limit),
        )
        return [dict(row) for row in rows]

    async def has_progress_since(
        self,
        user_id: int,
        module: str,
        since: datetime,
    ) -> bool:
        language = await self.get_learning_language(user_id)
        row = await self.fetchone(
            """
            SELECT id FROM progress
            WHERE user_id = ? AND language = ?
              AND module = ? AND completed_at >= ?
            LIMIT 1
            """,
            (user_id, language, module, since),
        )
        return row is not None

    async def reminder_sent_since(
        self,
        user_id: int,
        reminder_type: str,
        since: datetime,
    ) -> bool:
        row = await self.fetchone(
            """
            SELECT id FROM reminder_events
            WHERE user_id = ? AND reminder_type = ? AND sent_at >= ?
            LIMIT 1
            """,
            (user_id, reminder_type, since),
        )
        return row is not None

    async def record_reminder_event(
        self,
        user_id: int,
        reminder_type: str,
    ) -> None:
        await self.execute(
            """
            INSERT INTO reminder_events (user_id, reminder_type)
            VALUES (?, ?)
            """,
            (user_id, reminder_type),
        )

    async def has_seen_release(self, user_id: int, release_id: str) -> bool:
        row = await self.fetchone(
            """
            SELECT user_id FROM release_views
            WHERE user_id = ? AND release_id = ?
            """,
            (user_id, release_id),
        )
        return row is not None

    async def mark_release_seen(self, user_id: int, release_id: str) -> None:
        await self.execute(
            """
            INSERT INTO release_views (user_id, release_id)
            VALUES (?, ?)
            ON CONFLICT(user_id, release_id) DO NOTHING
            """,
            (user_id, release_id),
        )

    async def get_cache(self, cache_key: str) -> dict[str, Any] | None:
        row = await self.fetchone("SELECT payload FROM exercise_cache WHERE cache_key = ?", (cache_key,))
        if not row:
            return None
        return json.loads(row["payload"])

    async def set_cache(self, cache_key: str, payload: dict[str, Any]) -> None:
        await self.execute(
            """
            INSERT INTO exercise_cache (cache_key, payload) VALUES (?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET payload = excluded.payload, created_at = CURRENT_TIMESTAMP
            """,
            (cache_key, json.dumps(payload, ensure_ascii=False)),
        )
