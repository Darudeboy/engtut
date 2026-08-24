import hashlib
import logging
import os
import sys

from aiohttp import web
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

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
from bot.main import create_bot
from bot.services.reminders import ReminderService
from bot.utils.context import AppContext, set_app_context

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def _webhook_path() -> str:
    path = os.getenv("WEBHOOK_PATH", "/webhook").strip()
    if not path.startswith("/"):
        path = f"/{path}"
    return path


def _webhook_secret(bot_token: str) -> str:
    configured = os.getenv("WEBHOOK_SECRET", "").strip()
    if configured:
        return configured
    return hashlib.sha256(bot_token.encode("utf-8")).hexdigest()


def _public_url() -> str:
    return (
        os.getenv("WEBHOOK_BASE_URL")
        or os.getenv("RENDER_EXTERNAL_URL")
        or ""
    ).rstrip("/")


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(onboarding_router)
    dispatcher.include_router(daily_router)
    dispatcher.include_router(menu_router)
    dispatcher.include_router(reading_router)
    dispatcher.include_router(vocabulary_router)
    dispatcher.include_router(grammar_router)
    dispatcher.include_router(writing_router)
    dispatcher.include_router(dialogue_router)
    dispatcher.include_router(listening_router)
    dispatcher.include_router(progress_router)
    return dispatcher


async def health_check(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "english-tutor-bot"})


def create_app() -> web.Application:
    settings = get_settings()
    logging.getLogger().setLevel(settings.log_level)

    public_url = _public_url()
    if not public_url:
        raise ValueError(
            "WEBHOOK_BASE_URL is required outside Render. "
            "Example: https://your-service.onrender.com"
        )

    app_context = AppContext.build(settings)
    set_app_context(app_context)

    bot = create_bot(settings)
    dispatcher = create_dispatcher()
    reminders = ReminderService(app_context.db, bot)
    webhook_path = _webhook_path()
    webhook_secret = _webhook_secret(settings.bot_token)
    webhook_url = f"{public_url}{webhook_path}"

    async def on_startup() -> None:
        await app_context.db.connect()
        await reminders.start()
        await bot.set_webhook(
            webhook_url,
            secret_token=webhook_secret,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
        logger.info("Telegram webhook configured: %s", webhook_url)

    async def on_shutdown() -> None:
        await reminders.stop()
        await app_context.db.close()

    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)

    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    webhook_handler = SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=webhook_secret,
    )
    webhook_handler.register(app, path=webhook_path)
    setup_application(app, dispatcher, bot=bot)
    return app


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "10000"))
    logger.info("Starting webhook server on %s:%s", host, port)
    web.run_app(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
