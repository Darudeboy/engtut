"""Smoke tests for English Tutor Bot."""
import asyncio
import os
import tempfile
from pathlib import Path

from bot.config import Settings
from bot.models.database import Database, _asyncpg_url, _postgres_query
from bot.models.progress import ProgressRepository
from bot.models.vocabulary import VocabularyRepository
from bot.services.deepseek import DeepSeekService
from bot.webhook import _webhook_secret


async def test_database() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        db = Database(Path(temp_dir) / "test.db")
        await db.connect()
        try:
            user = await db.get_or_create_user(12345, "smoke_test")
            assert user["user_id"] == 12345

            progress = ProgressRepository(db)
            await progress.record_lesson(
                12345, "reading", "test_lesson", score=100.0
            )
            weekly = await progress.get_weekly_summary_data(12345)
            assert weekly["lessons_completed"] == 1
            assert weekly["weekly_modules"][0]["module"] == "reading"

            vocabulary = VocabularyRepository(db)
            await vocabulary.add_word(
                12345, "hello", "привет", "greetings"
            )
            assert await vocabulary.get_words_learned_today(12345) == 1
            assert len(await vocabulary.get_due_reviews(12345)) == 1

            assert await db.touch_activity(12345) == 1
        finally:
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


def test_webhook_secret() -> None:
    original = os.environ.get("WEBHOOK_SECRET")
    try:
        os.environ["WEBHOOK_SECRET"] = "unsafe secret!"
        secret = _webhook_secret("test-token")
        assert len(secret) == 64
        assert secret.isalnum()
    finally:
        if original is None:
            os.environ.pop("WEBHOOK_SECRET", None)
        else:
            os.environ["WEBHOOK_SECRET"] = original
    print("webhook secret: OK")


def test_postgres_compatibility_helpers() -> None:
    query = "SELECT * FROM progress WHERE user_id = ? AND completed_at >= ?"
    assert _postgres_query(query).endswith(
        "WHERE user_id = $1 AND completed_at >= $2"
    )
    neon_url = (
        "postgresql://user:password@example.neon.tech/db"
        "?sslmode=require&channel_binding=require"
    )
    compatible_url = _asyncpg_url(neon_url)
    assert "sslmode=require" in compatible_url
    assert "channel_binding" not in compatible_url
    print("postgres compatibility: OK")


if __name__ == "__main__":
    test_imports()
    test_webhook_secret()
    test_postgres_compatibility_helpers()
    test_deepseek_fallback()
    asyncio.run(test_database())
    print("All smoke tests passed")
