from dataclasses import dataclass
from datetime import date
from typing import Any

from bot.models.database import Database


@dataclass
class UserProfile:
    user_id: int
    username: str | None
    level: str
    goal: str | None
    streak_days: int
    onboarding_completed: bool
    writing_level: int
    learning_language: str


class UserRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_profile(self, user_id: int, username: str | None = None) -> UserProfile:
        row = await self.db.get_or_create_user(user_id, username)
        return UserProfile(
            user_id=row["user_id"],
            username=row.get("username"),
            level=row.get("level", "Pre-A1"),
            goal=row.get("goal"),
            streak_days=int(row.get("streak_days") or 0),
            onboarding_completed=bool(row.get("onboarding_completed")),
            writing_level=int(row.get("writing_level") or 1),
            learning_language=str(row.get("learning_language") or "english"),
        )

    async def complete_onboarding(
        self,
        user_id: int,
        level: str,
        goal: str,
        reminder_time: str | None,
    ) -> None:
        await self.db.update_user(
            user_id,
            level=level,
            goal=goal,
            reminder_time=reminder_time,
            onboarding_completed=1,
        )
