import re
from datetime import UTC, datetime, time
from typing import Any

from bot.models.database import Database

MODULE_LABELS = {
    "reading": "чтение",
    "grammar": "грамматику",
    "writing": "письмо",
    "listening": "аудирование",
    "dialogue": "диалог",
}

INTENT_KEYWORDS = {
    "grammar": ("грамматик", "grammar"),
    "reading": ("чтени", "почита", "reading"),
    "vocabulary": ("словар", "новые слова", "повторить слова", "vocabulary"),
    "writing": ("письм", "writing"),
    "listening": ("аудирован", "послуша", "listening"),
    "dialogue": ("диалог", "поговорим", "поговорить", "dialogue"),
    "progress": ("прогресс", "статистик", "результат"),
    "daily": ("ежеднев", "задание дня", "daily"),
    "exam": ("экзамен", "повысить уровень", "exam"),
    "next": ("что дальше", "следующий шаг", "что мне делать"),
}

ACTION_WORDS = (
    "давай",
    "хочу",
    "начни",
    "начать",
    "открой",
    "покажи",
    "запусти",
    "перейди",
    "потренируем",
    "show",
    "start",
    "open",
    "practice",
    "let's",
)

EXACT_INTENTS = {
    "грамматика": "grammar",
    "grammar": "grammar",
    "чтение": "reading",
    "reading": "reading",
    "слова": "vocabulary",
    "vocabulary": "vocabulary",
    "письмо": "writing",
    "writing": "writing",
    "аудирование": "listening",
    "listening": "listening",
    "диалог": "dialogue",
    "dialogue": "dialogue",
    "прогресс": "progress",
    "статистика": "progress",
    "daily": "daily",
    "экзамен": "exam",
    "exam": "exam",
}


def detect_intent(text: str) -> str | None:
    normalized = re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip()
    short_text = normalized.strip("!?., ")
    if short_text in EXACT_INTENTS:
        return EXACT_INTENTS[short_text]
    if any(keyword in short_text for keyword in INTENT_KEYWORDS["next"]):
        return "next"
    if not any(word in normalized for word in ACTION_WORDS):
        return None
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return intent
    return None


async def build_learner_context(
    db: Database,
    user_id: int,
) -> dict[str, Any]:
    stats = await db.get_stats(user_id)
    weak_topics = await db.get_weak_topics(user_id, limit=5)
    recent_progress = await db.fetchall(
        """
        SELECT module, lesson_id, score, completed_at
        FROM progress
        WHERE user_id = ? AND completed = 1
        ORDER BY completed_at DESC, id DESC
        LIMIT 6
        """,
        (user_id,),
    )
    return {
        "level": stats["level"],
        "goal": stats["goal"],
        "streak_days": stats["streak_days"],
        "words_learning": stats["words_learning"],
        "words_mastered": stats["words_mastered"],
        "words_due": stats["words_due"],
        "accuracy": stats["accuracy"],
        "weak_topics": [dict(row) for row in weak_topics],
        "recent_progress": [dict(row) for row in recent_progress],
    }


async def recommend_next_step(
    db: Database,
    user_id: int,
    exclude_module: str | None = None,
) -> dict[str, str]:
    stats = await db.get_stats(user_id)
    if stats["words_due"] > 0 and exclude_module != "vocabulary":
        return {
            "intent": "vocabulary",
            "text": (
                f"Повтори {stats['words_due']} слов — сейчас это самый полезный шаг. "
                "Нажми «Слова»."
            ),
        }

    weak_topics = await db.get_weak_topics(user_id, limit=5)
    for topic in weak_topics:
        module = str(topic["module"])
        if module == exclude_module or module not in MODULE_LABELS:
            continue
        return {
            "intent": module,
            "text": (
                f"Закрепи {MODULE_LABELS[module]}: предыдущий результат по теме "
                f"«{_friendly_topic(str(topic['lesson_id']))}» — "
                f"{round(float(topic['avg_score']))}%."
            ),
        }

    utc_today = datetime.now(UTC).date()
    today_start = datetime.combine(utc_today, time.min)
    if not await db.has_progress_since(user_id, "daily", today_start):
        return {
            "intent": "daily",
            "text": "Пройди /daily: он соберёт слова, чтение и грамматику в одну сессию.",
        }

    goal_steps = {
        "travel": ("dialogue", "Попрактикуй диалог для путешествий."),
        "work": ("dialogue", "Попрактикуй рабочий диалог."),
        "hobby": ("listening", "Попробуй короткое аудирование по знакомой теме."),
        "exam": ("exam", "Проверь готовность к следующему уровню командой /exam."),
    }
    intent, text = goal_steps.get(
        stats.get("goal"),
        ("reading", "Прочитай новый короткий текст и закрепи лексику."),
    )
    return {"intent": intent, "text": text}


async def personalized_reminder_text(db: Database, user_id: int) -> str:
    user = await db.get_or_create_user(user_id)
    recommendation = await recommend_next_step(db, user_id)
    level = user.get("level", "Pre-A1")
    return (
        f"⏰ Время для английского. Твой уровень: {level}.\n\n"
        f"{recommendation['text']}"
    )


def _friendly_topic(lesson_id: str) -> str:
    return lesson_id.split(":", 1)[0].replace("_", " ")
