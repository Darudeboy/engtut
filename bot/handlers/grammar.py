import secrets

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.utils.content import GRAMMAR_TOPICS
from bot.utils.context import get_app_context
from bot.utils.keyboards import options_keyboard
from bot.utils.states import GrammarStates

router = Router()

@router.message(F.text == "📚 Грамматика")
async def start_grammar(
    message: Message,
    state: FSMContext,
    part_of_daily: bool = False,
    user_id_override: int | None = None,
) -> None:
    ctx = get_app_context()
    user_id = user_id_override or message.from_user.id
    session = ctx.user_sessions.setdefault(user_id, {})
    if not part_of_daily and session.get("daily"):
        session["daily"]["active"] = False
    user = await ctx.db.get_or_create_user(user_id)
    topic_index = int(user.get("grammar_topic_index") or 0) % len(GRAMMAR_TOPICS)
    topic = GRAMMAR_TOPICS[topic_index]
    level = user.get("level", "Pre-A1")
    cache_key = f"grammar:{level}:{topic}"
    lesson = await ctx.db.get_cache(cache_key)
    if not lesson:
        lesson = await ctx.deepseek.generate_grammar_exercise(topic, level)
        await ctx.db.set_cache(cache_key, lesson)

    session.update(
        {
            "grammar": lesson,
            "grammar_id": secrets.token_hex(4),
            "topic": topic,
            "topic_index": topic_index,
            "q_index": 0,
            "score": 0,
            "mistakes": 0,
        }
    )
    await state.set_state(GrammarStates.answering)
    await message.answer(f"📚 Тема: {topic}\n\n{lesson.get('explanation_ru', '')}")
    await _send_grammar_question(message, user_id)


@router.callback_query(GrammarStates.answering, F.data.startswith("grammar:answer:"))
async def grammar_answer(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = callback.from_user.id
    session = ctx.user_sessions.get(user_id, {})
    lesson = session.get("grammar", {})
    questions = lesson.get("questions", [])
    q_index = int(session.get("q_index", 0))
    parts = callback.data.split(":")
    expected_token = f"{session.get('grammar_id')}-{q_index}"
    if (
        len(parts) != 4
        or parts[-2] != expected_token
        or q_index >= len(questions)
    ):
        await callback.answer("Этот вопрос уже не активен", show_alert=True)
        return
    selected = int(parts[-1])
    question = questions[q_index]
    correct_idx = int(question.get("correct_index", 0))
    options = question.get("options", [])
    if not 0 <= selected < len(options) or not 0 <= correct_idx < len(options):
        await callback.answer("Некорректный вариант", show_alert=True)
        return
    correct = selected == correct_idx

    if correct:
        session["score"] = int(session.get("score", 0)) + 1
        feedback = "✅ Верно!"
    else:
        session["mistakes"] = int(session.get("mistakes", 0)) + 1
        hint = question.get("hint_ru", "")
        correct_option = question["options"][correct_idx]
        feedback = f"Почти! Правильно: {correct_option}"
        if hint:
            feedback += f"\n💡 {hint}"

    q_index += 1
    session["q_index"] = q_index
    ctx.user_sessions[user_id] = session
    await callback.message.edit_text(
        f"{callback.message.text}\n\n{feedback}",
        parse_mode=None,
    )
    await callback.answer()

    if q_index >= len(questions):
        score = session.get("score", 0)
        total = len(questions) or 1
        pct = round(score / total * 100, 1)
        topic_index = int(session.get("topic_index", 0))
        if pct >= 80:
            topic_index = (topic_index + 1) % len(GRAMMAR_TOPICS)
            await ctx.db.update_user(user_id, grammar_topic_index=topic_index)
        await ctx.progress.record_lesson(user_id, "grammar", session.get("topic", "grammar"), score=pct)
        await ctx.db.touch_activity(user_id)
        await state.clear()
        await callback.message.answer(f"📚 Грамматика завершена: {score}/{total} ({pct}%)")
        if await _continue_daily(callback.message, state, user_id, pct):
            return
        return
    await _send_grammar_question(callback.message, user_id)


async def _send_grammar_question(message: Message, user_id: int) -> None:
    ctx = get_app_context()
    session = ctx.user_sessions.get(user_id, {})
    lesson = session.get("grammar", {})
    questions = lesson.get("questions", [])
    q_index = int(session.get("q_index", 0))
    if q_index >= len(questions):
        return
    question = questions[q_index]
    token = f"{session.get('grammar_id')}-{q_index}"
    await message.answer(
        f"✏️ {question['prompt']}",
        reply_markup=options_keyboard(
            question["options"],
            "grammar:answer",
            token,
        ),
    )


async def _continue_daily(
    message: Message,
    state: FSMContext,
    user_id: int,
    score: float,
) -> bool:
    ctx = get_app_context()
    daily = ctx.user_sessions.get(user_id, {}).get("daily", {})
    if not daily.get("active"):
        return False
    from bot.handlers.daily import continue_daily

    await continue_daily(message, state, user_id, "grammar", score)
    return True
