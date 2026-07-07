from datetime import date, timedelta
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
    ) -> None:
        await self.db.execute(
            """
            INSERT INTO user_words (
                user_id, word, translation, transcription, theme,
                example_en, example_ru, next_review
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                word.lower(),
                translation,
                transcription,
                theme,
                example_en,
                example_ru,
                date.today().isoformat(),
            ),
        )

    async def get_words_count(self, user_id: int) -> int:
        row = await self.db.fetchone(
            "SELECT COUNT(*) AS cnt FROM user_words WHERE user_id = ?",
            (user_id,),
        )
        return int(row["cnt"]) if row else 0

    async def get_words_learned_today(self, user_id: int) -> int:
        row = await self.db.fetchone(
            """
            SELECT COUNT(*) AS cnt FROM user_words
            WHERE user_id = ? AND date(learned_at) = date('now')
            """,
            (user_id,),
        )
        return int(row["cnt"]) if row else 0

    async def user_has_word(self, user_id: int, word: str) -> bool:
        row = await self.db.fetchone(
            "SELECT id FROM user_words WHERE user_id = ? AND word = ?",
            (user_id, word.lower()),
        )
        return row is not None

    async def get_due_reviews(self, user_id: int, limit: int = 5) -> list[dict[str, Any]]:
        rows = await self.db.fetchall(
            """
            SELECT * FROM user_words
            WHERE user_id = ? AND (next_review IS NULL OR next_review <= ?)
            ORDER BY next_review ASC
            LIMIT ?
            """,
            (user_id, date.today().isoformat(), limit),
        )
        return [dict(row) for row in rows]

    async def review_word(self, user_id: int, word_id: int, quality: int) -> None:
        row = await self.db.fetchone(
            "SELECT * FROM user_words WHERE id = ? AND user_id = ?",
            (word_id, user_id),
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
                next_review.isoformat(),
                word_id,
            ),
        )
