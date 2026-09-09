import logging
from datetime import UTC, date, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.models.database import Database
from bot.services.coach import personalized_reminder_text, recommend_next_step

logger = logging.getLogger(__name__)


class ReminderService:
    def __init__(self, db: Database, bot) -> None:
        self.db = db
        self.bot = bot
        self.scheduler = AsyncIOScheduler()

    async def start(self) -> None:
        self.scheduler.add_job(self.send_reminders, CronTrigger(minute="*/30"))
        self.scheduler.add_job(self.send_inactivity_reminders, CronTrigger(hour=10, minute=0))
        self.scheduler.start()
        logger.info("Reminder scheduler started")

    async def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    async def send_reminders(self) -> None:
        now = datetime.now().strftime("%H:%M")
        utc_now = datetime.now(UTC).replace(tzinfo=None)
        today_start = datetime.combine(utc_now.date(), datetime.min.time())
        rows = await self.db.fetchall(
            "SELECT user_id, reminder_time FROM users WHERE reminder_time = ? AND onboarding_completed = 1",
            (now,),
        )
        for row in rows:
            user_id = int(row["user_id"])
            if await self.db.reminder_sent_since(
                user_id,
                "scheduled",
                today_start,
            ):
                continue
            try:
                text = await personalized_reminder_text(self.db, user_id)
                await self.bot.send_message(
                    user_id,
                    text,
                )
                await self.db.record_reminder_event(user_id, "scheduled")
            except Exception as exc:
                logger.warning("Failed to send reminder to %s: %s", user_id, exc)

    async def send_inactivity_reminders(self) -> None:
        inactive_since = date.today() - timedelta(days=2)
        rows = await self.db.fetchall(
            """
            SELECT user_id FROM users
            WHERE onboarding_completed = 1
              AND last_active IS NOT NULL
              AND last_active <= ?
            """,
            (inactive_since,),
        )
        for row in rows:
            user_id = int(row["user_id"])
            if await self.db.reminder_sent_since(
                user_id,
                "inactivity",
                datetime.now(UTC).replace(tzinfo=None) - timedelta(days=3),
            ):
                continue
            try:
                recommendation = await recommend_next_step(self.db, user_id)
                await self.bot.send_message(
                    user_id,
                    "👋 Давно не виделись! Даже короткая практика помогает.\n\n"
                    + recommendation["text"],
                )
                await self.db.record_reminder_event(user_id, "inactivity")
            except Exception as exc:
                logger.warning("Failed to send inactivity reminder to %s: %s", user_id, exc)
