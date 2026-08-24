import json
import logging
from datetime import date, datetime
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
DELETE FROM user_words
WHERE id NOT IN (
    SELECT MIN(id) FROM user_words GROUP BY user_id, word
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_words_user_word
ON user_words(user_id, word);

CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    module TEXT,
    lesson_id TEXT,
    completed INTEGER DEFAULT 0,
    score REAL,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS dialogues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
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
DELETE FROM user_words
WHERE id NOT IN (
    SELECT MIN(id) FROM user_words GROUP BY user_id, word
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_words_user_word
ON user_words(user_id, word);

CREATE TABLE IF NOT EXISTS progress (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    module TEXT,
    lesson_id TEXT,
    completed INTEGER DEFAULT 0,
    score DOUBLE PRECISION,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS dialogues (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
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
            logger.info("PostgreSQL database initialized")
            return

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._sqlite = await aiosqlite.connect(self.db_path)
        self._sqlite.row_factory = aiosqlite.Row
        await self._sqlite.executescript(SQLITE_SCHEMA)
        await self._sqlite.commit()
        logger.info("Database initialized at %s", self.db_path)

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
        if row:
            return dict(row)
        await self.execute(
            """
            INSERT INTO users (user_id, username, last_active) VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO NOTHING
            """,
            (user_id, username, date.today()),
        )
        row = await self.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return dict(row) if row else {}

    async def update_user(self, user_id: int, **fields: Any) -> None:
        if not fields:
            return
        columns = ", ".join(f"{key} = ?" for key in fields)
        values = tuple(fields.values()) + (user_id,)
        await self.execute(f"UPDATE users SET {columns} WHERE user_id = ?", values)

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
    ) -> None:
        await self.execute(
            """
            INSERT INTO progress (user_id, module, lesson_id, completed, score, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, module, lesson_id, int(completed), score, datetime.utcnow()),
        )

    async def get_stats(self, user_id: int) -> dict[str, Any]:
        user = await self.get_or_create_user(user_id)
        words_row = await self.fetchone(
            """
            SELECT
                COUNT(*) AS introduced,
                COALESCE(SUM(CASE WHEN repetitions < 3 THEN 1 ELSE 0 END), 0) AS learning,
                COALESCE(SUM(CASE WHEN repetitions >= 3 THEN 1 ELSE 0 END), 0) AS mastered
            FROM user_words
            WHERE user_id = ?
            """,
            (user_id,),
        )
        due_row = await self.fetchone(
            """
            SELECT COUNT(*) AS cnt
            FROM user_words
            WHERE user_id = ? AND (next_review IS NULL OR next_review <= ?)
            """,
            (user_id, date.today()),
        )
        lessons_row = await self.fetchone(
            "SELECT COUNT(*) AS cnt FROM progress WHERE user_id = ? AND completed = 1",
            (user_id,),
        )
        accuracy_row = await self.fetchone(
            """
            SELECT AVG(score) AS avg_score
            FROM progress
            WHERE user_id = ?
              AND score IS NOT NULL
              AND module IN ('reading', 'grammar', 'writing', 'listening')
            """,
            (user_id,),
        )
        achievements = await self.fetchall(
            "SELECT achievement_code, unlocked_at FROM achievements WHERE user_id = ? ORDER BY unlocked_at",
            (user_id,),
        )
        return {
            "level": user.get("level", "Pre-A1"),
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
