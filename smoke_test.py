"""Smoke tests for English Tutor Bot."""
import asyncio
import json
import os
import tempfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from bot.config import Settings
from bot.handlers.exam import exam_passed
from bot.handlers.writing import _normalize
from bot.models.database import Database, _asyncpg_url, _postgres_query
from bot.models.progress import ProgressRepository
from bot.models.vocabulary import VocabularyRepository
from bot.services.coach import (
    build_learner_context,
    detect_intent,
    recommend_next_step,
)
from bot.services.deepseek import DeepSeekService
from bot.utils.content import WRITING_STAGES
from bot.utils.exam_content import EXAMS, SECTION_LABELS
from bot.utils.releases import BOT_COMMANDS, CURRENT_RELEASE_ID, CURRENT_RELEASE_TEXT
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
            await progress.record_lesson(
                12345, "writing", "test_writing", score=70.0
            )
            assert await db.get_lesson_attempt_count(12345, "writing") == 1
            weak_topics = await db.get_weak_topics(12345)
            assert weak_topics[0]["module"] == "writing"
            await progress.record_lesson(
                12345, "writing", "test_writing", score=100.0
            )
            assert await db.get_weak_topics(12345) == []
            assert await db.has_progress_since(
                12345,
                "reading",
                datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1),
            )

            await db.add_tutor_message(12345, "user", "Hello")
            await db.add_tutor_message(12345, "assistant", "Hi!")
            tutor_history = await db.get_recent_tutor_messages(12345)
            assert [item["role"] for item in tutor_history] == ["user", "assistant"]
            await db.execute(
                """
                INSERT INTO dialogues (user_id, scenario, messages, feedback)
                VALUES (?, ?, ?, ?)
                """,
                (12345, "test", "[]", "test"),
            )
            await db.clear_ai_history(12345)
            assert await db.get_recent_tutor_messages(12345) == []
            assert await db.fetchone(
                "SELECT id FROM dialogues WHERE user_id = ?",
                (12345,),
            ) is None

            assert not await db.reminder_sent_since(
                12345,
                "scheduled",
                datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1),
            )
            await db.record_reminder_event(12345, "scheduled")
            assert await db.reminder_sent_since(
                12345,
                "scheduled",
                datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1),
            )
            assert not await db.has_seen_release(12345, CURRENT_RELEASE_ID)
            await db.mark_release_seen(12345, CURRENT_RELEASE_ID)
            await db.mark_release_seen(12345, CURRENT_RELEASE_ID)
            assert await db.has_seen_release(12345, CURRENT_RELEASE_ID)

            vocabulary = VocabularyRepository(db)
            await vocabulary.add_word(
                12345, "hello", "привет", "greetings"
            )
            await vocabulary.add_word(
                12345, "hello", "привет", "greetings"
            )
            assert await vocabulary.get_words_learned_today(12345) == 1
            assert (await vocabulary.get_recent_words(12345))[0]["word"] == "hello"
            assert len(await vocabulary.get_due_reviews(12345)) == 0
            stats = await db.get_stats(12345)
            assert stats["words_introduced"] == 1
            assert stats["words_learning"] == 1
            assert stats["words_mastered"] == 0
            assert stats["accuracy"] == 90.0

            await db.execute(
                "UPDATE user_words SET next_review = ? WHERE user_id = ?",
                (date.today(), 12345),
            )
            assert len(await vocabulary.get_due_reviews(12345)) == 1
            word_id = (await vocabulary.get_due_reviews(12345))[0]["id"]
            for _ in range(3):
                await vocabulary.review_word(12345, word_id, quality=5)
            stats = await db.get_stats(12345)
            assert stats["words_learning"] == 0
            assert stats["words_mastered"] == 1
            context = await build_learner_context(db, 12345)
            assert context["level"] == "Pre-A1"
            recommendation = await recommend_next_step(
                db,
                12345,
                exclude_module="writing",
            )
            assert recommendation["intent"] in {
                "daily",
                "reading",
                "grammar",
                "listening",
                "dialogue",
            }

            section_scores = {
                section: {"correct": 4, "total": 5}
                for section in SECTION_LABELS
            }
            await db.record_exam_attempt(
                12345,
                "A1",
                "A2",
                12,
                15,
                80.0,
                True,
                section_scores,
            )
            attempt = await db.get_latest_exam_attempt(12345, "A2")
            assert attempt is not None
            assert attempt["passed"] == 1
            assert attempt["section_scores"]["reading"]["correct"] == 4

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
    assert len(lesson["questions"]) == 4
    grammar = asyncio.run(
        service.generate_grammar_exercise("to be", "Pre-A1", 0)
    )
    assert len(grammar["questions"]) == 5
    writing = asyncio.run(
        service.check_writing_task(
            prompt="Describe your morning.",
            requirements="Write two actions.",
            reference="I get up and have breakfast.",
            user_answer="I get up early and have breakfast with my family.",
            level="A1",
            min_words=8,
        )
    )
    assert writing["status"] == "correct"
    listening = asyncio.run(
        service.generate_listening_lesson("daily life", "A1", 0)
    )
    assert listening["transcript"]
    assert len(listening["questions"]) == 3
    dialogue = asyncio.run(
        service.assess_dialogue(
            "coffee",
            [
                {"role": "user", "content": "I would like a coffee."},
                {"role": "user", "content": "A small coffee, please."},
                {"role": "user", "content": "How much is it?"},
            ],
            "A1",
            ["order a drink", "choose a size", "ask about the price"],
        )
    )
    assert 0 <= dialogue["score"] <= 100
    coach = asyncio.run(
        service.coach_reply(
            {"level": "A1", "words_due": 0},
            [],
            "Can we practise English?",
        )
    )
    assert coach
    print("deepseek fallback: OK")


def test_imports() -> None:
    from bot.handlers import onboarding_router  # noqa: F401
    from bot.main import main  # noqa: F401

    print("imports: OK")


def test_wordlists() -> None:
    words: list[str] = []
    for path in Path("data/wordlists").glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["theme"]
        words.extend(item["word"].lower() for item in payload["words"])
    assert len(words) >= 190
    assert len(words) == len(set(words))
    print(f"wordlists: OK ({len(words)} words)")


def test_exam_content() -> None:
    for target_level, exam in EXAMS.items():
        questions = exam["questions"]
        assert len(questions) == 15, target_level
        for section in SECTION_LABELS:
            assert sum(q["section"] == section for q in questions) == 5
        for question in questions:
            assert 0 <= question["correct_index"] < len(question["options"])

    balanced_pass = {
        section: {"correct": 4, "total": 5}
        for section in SECTION_LABELS
    }
    weak_section = {
        "vocabulary": {"correct": 5, "total": 5},
        "grammar": {"correct": 5, "total": 5},
        "reading": {"correct": 2, "total": 5},
    }
    assert exam_passed(12, 15, balanced_pass)
    assert not exam_passed(12, 15, weak_section)
    assert not exam_passed(11, 15, balanced_pass)
    print("exam content: OK")


def test_writing_content() -> None:
    assert sorted(WRITING_STAGES) == list(range(1, 9))
    task_ids: list[str] = []
    for tasks in WRITING_STAGES.values():
        assert len(tasks) >= 3
        for task in tasks:
            task_ids.append(task["id"])
            if task.get("free"):
                assert task["min_words"] > 0
                assert task["requirements"]
                assert task["reference"]
            else:
                assert task["answer"]
    assert len(task_ids) == len(set(task_ids))
    assert _normalize("I am a student.") == _normalize("I am a student")
    print(f"writing content: OK ({len(task_ids)} tasks)")


def test_coach_intents() -> None:
    assert detect_intent("Давай грамматику") == "grammar"
    assert detect_intent("Покажи мой прогресс") == "progress"
    assert detect_intent("Что мне делать дальше?") == "next"
    assert detect_intent("Как прошёл твой день?") is None
    assert detect_intent("Please show me an example sentence") is None
    assert detect_intent("Let us openly discuss grammar") is None
    assert detect_intent("Я хочу написать письмо другу") is None
    print("coach intents: OK")


def test_release_notes() -> None:
    commands = [item.command for item in BOT_COMMANDS]
    assert commands == [
        "start",
        "daily",
        "exam",
        "stats",
        "whatsnew",
        "forget",
        "help",
    ]
    assert len(commands) == len(set(commands))
    assert CURRENT_RELEASE_ID
    assert "AI-наставник" in CURRENT_RELEASE_TEXT
    print("release notes: OK")


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
    test_wordlists()
    test_exam_content()
    test_writing_content()
    test_coach_intents()
    test_release_notes()
    test_webhook_secret()
    test_postgres_compatibility_helpers()
    test_deepseek_fallback()
    asyncio.run(test_database())
    print("All smoke tests passed")
