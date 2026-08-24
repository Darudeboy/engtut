from datetime import datetime, timedelta
from typing import Any

from bot.models.database import Database


class ProgressRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def record_lesson(
        self,
        user_id: int,
        module: str,
        lesson_id: str,
        score: float | None = None,
    ) -> None:
        await self.db.add_progress(user_id, module, lesson_id, score=score, completed=True)

    async def get_weekly_summary_data(self, user_id: int) -> dict[str, Any]:
        stats = await self.db.get_stats(user_id)
        week_start = datetime.utcnow() - timedelta(days=7)
        recent = await self.db.fetchall(
            """
            SELECT module, COUNT(*) AS cnt, AVG(score) AS avg_score
            FROM progress
            WHERE user_id = ? AND completed_at >= ?
            GROUP BY module
            """,
            (user_id, week_start),
        )
        return {
            **stats,
            "weekly_modules": [dict(row) for row in recent],
        }
