"""Smoke tests for English Tutor Bot."""
import asyncio
from pathlib import Path

from bot.models.database import Database
from bot.services.deepseek import DeepSeekService
from bot.config import Settings


async def test_database() -> None:
    db = Database(Path("data/test_smoke.db"))
    await db.connect()
    user = await db.get_or_create_user(12345, "smoke_test")
    assert user["user_id"] == 12345
    await db.add_progress(12345, "reading", "test_lesson", score=100.0)
    stats = await db.get_stats(12345)
    assert stats["lessons_completed"] >= 1
    await db.close()
    print("database: OK")


def test_deepseek_fallback() -> None:
    settings = Settings(
        bot_token="test",
        deepseek_api_key="",
        deepseek_base_url="https://api.deepseek.com/v1",
        deepseek_model="deepseek-chat",
        database_path=Path("data/test.db"),
        log_level="INFO",
    )
    service = DeepSeekService(settings)
    lesson = asyncio.run(service.generate_reading_lesson("greetings"))
    assert "questions" in lesson
    assert len(lesson["questions"]) >= 1
    print("deepseek fallback: OK")


def test_imports() -> None:
    from bot.handlers import onboarding_router  # noqa: F401
    from bot.main import main  # noqa: F401

    print("imports: OK")


if __name__ == "__main__":
    test_imports()
    test_deepseek_fallback()
    asyncio.run(test_database())
    print("All smoke tests passed")
