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

COMMON_ACTION = (
    r"\b(?:давай|хочу\s+(?:учить|повторить|потренировать)|"
    r"нач(?:ни|ать)|открой|покажи|запусти|перейди|"
    r"потрениру\w*|show|start|open|practice|let['’]?s)\b"
)

LAUNCH_PATTERNS = {
    "grammar": rf"{COMMON_ACTION}.{{0,24}}\b(?:грамматик\w*|grammar)\b",
    "reading": rf"{COMMON_ACTION}.{{0,24}}\b(?:чтени\w*|почита\w*|reading)\b",
    "vocabulary": (
        rf"{COMMON_ACTION}.{{0,24}}"
        r"(?:\bсловар\w*\b|\bслов\w*\b|\bvocabulary\b)"
    ),
    "listening": rf"{COMMON_ACTION}.{{0,24}}\b(?:аудирован\w*|послуша\w*|listening)\b",
    "dialogue": rf"{COMMON_ACTION}.{{0,24}}\b(?:диалог\w*|поговор\w*|dialogue)\b",
    "progress": rf"{COMMON_ACTION}.{{0,24}}\b(?:прогресс\w*|статистик\w*|results?)\b",
    "daily": rf"{COMMON_ACTION}.{{0,24}}(?:ежеднев\w*|задани\w*\s+дня|\bdaily\b)",
    "exam": rf"{COMMON_ACTION}.{{0,24}}(?:экзамен\w*|повысить\s+уровень|\bexam\b)",
    # Intentionally excludes “хочу написать письмо другу”.
    "writing": (
        r"\b(?:давай|нач(?:ни|ать)|открой|запусти|перейди|"
        r"потрениру\w*|start|open|practice|let['’]?s)\b"
        r".{0,24}\b(?:письм\w*|writing)\b"
    ),
}


def detect_intent(text: str) -> str | None:
    normalized = re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip()
    short_text = normalized.strip("!?., ")
    if short_text in EXACT_INTENTS:
        return EXACT_INTENTS[short_text]
    if re.search(
        r"\b(?:что\s+(?:мне\s+)?(?:делать\s+)?дальше|следующ\w*\s+шаг)\b",
        short_text,
    ):
        return "next"
    for intent, pattern in LAUNCH_PATTERNS.items():
        if re.search(pattern, normalized):
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
