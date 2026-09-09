from datetime import date, datetime, time, timedelta
from typing import Any

from bot.models.database import Database
from bot.services.sm2 import sm2_update


class VocabularyRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def add_word(
        self,
        user_id: int,
        word: str,
        translation: str,
        theme: str,
        transcription: str = "",
        example_en: str = "",
        example_ru: str = "",
        language: str | None = None,
    ) -> None:
        language = language or await self.db.get_learning_language(user_id)
        await self.db.execute(
            """
            INSERT INTO user_words (
                user_id, language, word, translation, transcription, theme,
                example_en, example_ru, next_review
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, language, word) DO NOTHING
            """,
            (
                user_id,
                language,
                word.lower(),
                translation,
                transcription,
                theme,
                example_en,
                example_ru,
                date.today() + timedelta(days=1),
            ),
        )

    async def get_words_count(
        self,
        user_id: int,
        language: str | None = None,
    ) -> int:
        language = language or await self.db.get_learning_language(user_id)
        row = await self.db.fetchone(
            """
            SELECT COUNT(*) AS cnt FROM user_words
            WHERE user_id = ? AND language = ?
            """,
            (user_id, language),
        )
        return int(row["cnt"]) if row else 0

    async def get_words_learned_today(self, user_id: int) -> int:
        language = await self.db.get_learning_language(user_id)
        today = date.today()
        day_start = datetime.combine(today, time.min)
        next_day_start = day_start + timedelta(days=1)
        row = await self.db.fetchone(
            """
            SELECT COUNT(*) AS cnt FROM user_words
            WHERE user_id = ? AND language = ?
              AND learned_at >= ? AND learned_at < ?
            """,
            (user_id, language, day_start, next_day_start),
        )
        return int(row["cnt"]) if row else 0

    async def get_due_count(self, user_id: int) -> int:
        language = await self.db.get_learning_language(user_id)
        row = await self.db.fetchone(
            """
            SELECT COUNT(*) AS cnt FROM user_words
            WHERE user_id = ? AND language = ?
              AND (next_review IS NULL OR next_review <= ?)
            """,
            (user_id, language, date.today()),
        )
        return int(row["cnt"]) if row else 0

    async def user_has_word(
        self,
        user_id: int,
        word: str,
        language: str | None = None,
    ) -> bool:
        language = language or await self.db.get_learning_language(user_id)
        row = await self.db.fetchone(
            """
            SELECT id FROM user_words
            WHERE user_id = ? AND language = ? AND word = ?
            """,
            (user_id, language, word.lower()),
        )
        return row is not None

    async def get_recent_words(
        self,
        user_id: int,
        limit: int = 5,
    ) -> list[dict[str, str]]:
        language = await self.db.get_learning_language(user_id)
        rows = await self.db.fetchall(
            """
            SELECT word, translation FROM user_words
            WHERE user_id = ? AND language = ?
            ORDER BY learned_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, language, limit),
        )
        return [
            {
                "word": str(row["word"]),
                "translation": str(row["translation"]),
            }
            for row in rows
        ]

    async def get_due_reviews(self, user_id: int, limit: int = 5) -> list[dict[str, Any]]:
        language = await self.db.get_learning_language(user_id)
        rows = await self.db.fetchall(
            """
            SELECT * FROM user_words
            WHERE user_id = ? AND language = ?
              AND (next_review IS NULL OR next_review <= ?)
            ORDER BY next_review ASC
            LIMIT ?
            """,
            (user_id, language, date.today(), limit),
        )
        return [dict(row) for row in rows]

    async def review_word(
        self,
        user_id: int,
        word_id: int,
        quality: int,
        language: str | None = None,
    ) -> None:
        language = language or await self.db.get_learning_language(user_id)
        row = await self.db.fetchone(
            """
            SELECT * FROM user_words
            WHERE id = ? AND user_id = ? AND language = ?
            """,
            (word_id, user_id, language),
        )
        if not row:
            return
        result = sm2_update(
            quality=quality,
            repetitions=int(row["repetitions"] or 0),
            ease_factor=float(row["ease_factor"] or 2.5),
            interval_days=int(row["interval_days"] or 1),
        )
        next_review = date.today() + timedelta(days=result.interval_days)
        await self.db.execute(
            """
            UPDATE user_words
            SET repetitions = ?, ease_factor = ?, interval_days = ?, next_review = ?
            WHERE id = ?
            """,
            (
                result.repetitions,
                result.ease_factor,
                result.interval_days,
                next_review,
                word_id,
            ),
        )
