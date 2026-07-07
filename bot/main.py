import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings
from bot.handlers.daily import router as daily_router
from bot.handlers.dialogue import router as dialogue_router
from bot.handlers.grammar import router as grammar_router
from bot.handlers.listening import router as listening_router
from bot.handlers.menu import router as menu_router
from bot.handlers.onboarding import router as onboarding_router
from bot.handlers.progress import router as progress_router
from bot.handlers.reading import router as reading_router
from bot.handlers.vocabulary import router as vocabulary_router
from bot.handlers.writing import router as writing_router
from bot.services.reminders import ReminderService
from bot.utils.context import AppContext

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    logging.getLogger().setLevel(settings.log_level)

    app_context = AppContext.build(settings)
    await app_context.db.connect()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    bot["app_context"] = app_context

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(onboarding_router)
    dp.include_router(daily_router)
    dp.include_router(menu_router)
    dp.include_router(reading_router)
    dp.include_router(vocabulary_router)
    dp.include_router(grammar_router)
    dp.include_router(writing_router)
    dp.include_router(dialogue_router)
    dp.include_router(listening_router)
    dp.include_router(progress_router)

    reminders = ReminderService(app_context.db, bot)
    await reminders.start()

    logger.info("English Tutor Bot started")
    try:
        await dp.start_polling(bot)
    finally:
        await reminders.stop()
        await app_context.db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
