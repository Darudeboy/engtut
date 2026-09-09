from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.utils.context import get_app_context
from bot.utils.states import DailyStates

router = Router()

GOAL_THEMES = {
    "travel": "travel",
    "work": "work",
    "hobby": "hobbies",
    "exam": "verbs",
}


@router.message(Command("daily"))
async def daily_session(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    profile = await ctx.users.get_profile(user_id, message.from_user.username)

    if not profile.onboarding_completed:
        await message.answer("Сначала пройди онбординг: /start")
        return

    await state.clear()
    session = ctx.user_sessions.setdefault(user_id, {})
    session["daily"] = {
        "active": True,
        "phase": "review",
        "completed": [],
        "scores": {},
        "theme": GOAL_THEMES.get(profile.goal),
        "language": profile.learning_language,
    }
    await state.set_state(DailyStates.in_session)
    await message.answer(
        "🌟 Задание дня (10–15 минут)\n\n"
        "1️⃣ Повторение слов\n"
        "2️⃣ 5 новых слов\n"
        "3️⃣ Короткое чтение\n"
        "4️⃣ Грамматика\n\n"
        "Я сам проведу тебя по всем этапам. Начинаем с повторения."
    )

    from bot.handlers.vocabulary import start_review_session

    if not await start_review_session(message, state, user_id):
        await message.answer("На сегодня обязательных повторений нет.")
        await continue_daily(message, state, user_id, "review")


async def continue_daily(
    message: Message,
    state: FSMContext,
    user_id: int,
    completed_step: str,
    score: float | None = None,
) -> None:
    ctx = get_app_context()
    session = ctx.user_sessions.setdefault(user_id, {})
    daily = session.get("daily", {})
    if not daily.get("active"):
        return
    if daily.get("phase") != completed_step:
        return

    completed = daily.setdefault("completed", [])
    if completed_step not in completed:
        completed.append(completed_step)
    if score is not None:
        daily.setdefault("scores", {})[completed_step] = score

    if completed_step == "review":
        daily["phase"] = "vocabulary"
        await message.answer("Шаг 2/4 · Новые слова")
        learned_today = await ctx.vocabulary.get_words_learned_today(user_id)
        needed = max(0, ctx.settings.new_words_per_day - learned_today)
        if needed:
            from bot.handlers.vocabulary import learn_new_batch

            await learn_new_batch(
                message,
                state,
                user_id,
                theme_filter=daily.get("theme"),
                batch_limit=needed,
            )
        else:
            await message.answer("Базовая порция новых слов сегодня уже выполнена.")
            await continue_daily(message, state, user_id, "vocabulary")
        return

    if completed_step == "vocabulary":
        daily["phase"] = "reading"
        await message.answer("Шаг 3/4 · Чтение")
        from bot.handlers.reading import start_reading

        await start_reading(
            message,
            state,
            part_of_daily=True,
            user_id_override=user_id,
        )
        return

    if completed_step == "reading":
        daily["phase"] = "grammar"
        await message.answer("Шаг 4/4 · Грамматика")
        from bot.handlers.grammar import start_grammar

        await start_grammar(
            message,
            state,
            part_of_daily=True,
            user_id_override=user_id,
        )
        return

    if completed_step == "grammar":
        daily["active"] = False
        daily["phase"] = "completed"
        await state.clear()
        await ctx.progress.record_lesson(
            user_id,
            "daily",
            "guided_session",
            score=_average_score(daily.get("scores", {})),
            language=daily.get("language", "english"),
        )
        streak = await ctx.db.touch_activity(user_id)
        if streak >= 7:
            await ctx.db.unlock_achievement(user_id, "seven_day_streak")
        stats = await ctx.db.get_stats(user_id)
        scores = daily.get("scores", {})
        score_lines = []
        if "reading" in scores:
            score_lines.append(f"Чтение: {scores['reading']}%")
        if "grammar" in scores:
            score_lines.append(f"Грамматика: {scores['grammar']}%")
        score_text = "\n".join(score_lines)
        await message.answer(
            "✅ Ежедневная сессия завершена!\n\n"
            f"{score_text}\n"
            f"🔥 Streak: {streak} дн.\n"
            f"🧠 Слов в изучении: {stats['words_learning']}\n"
            f"✅ Слов освоено: {stats['words_mastered']}"
        )
        from bot.handlers.tutor import send_next_step

        await send_next_step(message, user_id)


def _average_score(scores: dict[str, float]) -> float | None:
    values = [float(value) for value in scores.values()]
    if not values:
        return None
    return round(sum(values) / len(values), 1)
