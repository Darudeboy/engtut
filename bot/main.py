import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings
from bot.handlers.daily import router as daily_router
from bot.handlers.dialogue import router as dialogue_router
from bot.handlers.exam import router as exam_router
from bot.handlers.grammar import router as grammar_router
from bot.handlers.listening import router as listening_router
from bot.handlers.menu import router as menu_router
from bot.handlers.onboarding import router as onboarding_router
from bot.handlers.progress import router as progress_router
from bot.handlers.reading import router as reading_router
from bot.handlers.tutor import router as tutor_router
from bot.handlers.vocabulary import router as vocabulary_router
from bot.handlers.writing import router as writing_router
from bot.services.reminders import ReminderService
from bot.utils.context import AppContext, set_app_context

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def create_bot(settings) -> Bot:
    session_kwargs = {}
    if settings.bot_proxy:
        session_kwargs["proxy"] = settings.bot_proxy
        logger.info("Using proxy for Telegram API: %s", settings.bot_proxy)
    session = AiohttpSession(**session_kwargs)
    return Bot(
        token=settings.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


async def main() -> None:
    settings = get_settings()
    logging.getLogger().setLevel(settings.log_level)

    app_context = AppContext.build(settings)
    await app_context.db.connect()
    set_app_context(app_context)

    bot = create_bot(settings)

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(onboarding_router)
    dp.include_router(daily_router)
    dp.include_router(exam_router)
    dp.include_router(menu_router)
    dp.include_router(reading_router)
    dp.include_router(vocabulary_router)
    dp.include_router(grammar_router)
    dp.include_router(writing_router)
    dp.include_router(dialogue_router)
    dp.include_router(listening_router)
    dp.include_router(progress_router)
    dp.include_router(tutor_router)

    reminders = ReminderService(app_context.db, bot)
    await reminders.start()

    logger.info("English Tutor Bot started")
    try:
        await dp.start_polling(bot)
    except TelegramNetworkError as exc:
        logger.error("Cannot connect to Telegram API: %s", exc)
        print(
            "\nНе удалось подключиться к api.telegram.org.\n"
            "Возможные решения:\n"
            "1. Включите VPN\n"
            "2. Укажите прокси в .env:\n"
            "   BOT_PROXY=socks5://127.0.0.1:1080\n"
            "   или BOT_PROXY=http://127.0.0.1:8080\n"
            "3. Проверьте интернет и файрвол\n",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    finally:
        await reminders.stop()
        await app_context.db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
