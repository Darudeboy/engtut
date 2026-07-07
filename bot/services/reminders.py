import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.models.database import Database

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
        rows = await self.db.fetchall(
            "SELECT user_id, reminder_time FROM users WHERE reminder_time = ? AND onboarding_completed = 1",
            (now,),
        )
        for row in rows:
            try:
                await self.bot.send_message(
                    row["user_id"],
                    "⏰ Время для короткого урока английского! Нажми /daily 🌟",
                )
            except Exception as exc:
                logger.warning("Failed to send reminder to %s: %s", row["user_id"], exc)

    async def send_inactivity_reminders(self) -> None:
        rows = await self.db.fetchall(
            """
            SELECT user_id FROM users
            WHERE onboarding_completed = 1
              AND last_active IS NOT NULL
              AND julianday('now') - julianday(last_active) >= 2
            """
        )
        for row in rows:
            try:
                await self.bot.send_message(
                    row["user_id"],
                    "👋 Давно не виделись! Даже 10 минут в день помогают. Попробуй /daily",
                )
            except Exception as exc:
                logger.warning("Failed to send inactivity reminder to %s: %s", row["user_id"], exc)
