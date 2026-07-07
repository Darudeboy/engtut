import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)

SCHEMA = """
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


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()
        logger.info("Database initialized at %s", self.db_path)

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if not self._conn:
            raise RuntimeError("Database is not connected")
        return self._conn

    async def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        await self.conn.execute(query, params)
        await self.conn.commit()

    async def fetchone(self, query: str, params: tuple[Any, ...] = ()) -> aiosqlite.Row | None:
        cursor = await self.conn.execute(query, params)
        return await cursor.fetchone()

    async def fetchall(self, query: str, params: tuple[Any, ...] = ()) -> list[aiosqlite.Row]:
        cursor = await self.conn.execute(query, params)
        return await cursor.fetchall()

    async def get_or_create_user(self, user_id: int, username: str | None = None) -> dict[str, Any]:
        row = await self.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if row:
            return dict(row)
        await self.execute(
            "INSERT INTO users (user_id, username, last_active) VALUES (?, ?, ?)",
            (user_id, username, date.today().isoformat()),
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
            last_date = date.fromisoformat(last_active)
            delta = (today - last_date).days
            if delta == 1:
                streak += 1
            elif delta > 1:
                streak = 1
            elif delta == 0:
                pass
        else:
            streak = 1

        await self.update_user(user_id, streak_days=streak, last_active=today.isoformat())
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
            (user_id, module, lesson_id, int(completed), score, datetime.utcnow().isoformat()),
        )

    async def get_stats(self, user_id: int) -> dict[str, Any]:
        user = await self.get_or_create_user(user_id)
        words_row = await self.fetchone(
            "SELECT COUNT(*) AS cnt FROM user_words WHERE user_id = ?", (user_id,)
        )
        lessons_row = await self.fetchone(
            "SELECT COUNT(*) AS cnt FROM progress WHERE user_id = ? AND completed = 1",
            (user_id,),
        )
        accuracy_row = await self.fetchone(
            "SELECT AVG(score) AS avg_score FROM progress WHERE user_id = ? AND score IS NOT NULL",
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
            "words_learned": words_row["cnt"] if words_row else 0,
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
