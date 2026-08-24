import secrets

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.utils.context import get_app_context
from bot.utils.keyboards import options_keyboard
from bot.utils.states import ReadingStates

router = Router()

GOAL_READING_TOPICS = {
    "travel": "a simple trip",
    "work": "a simple work day",
    "hobby": "free time and hobbies",
    "exam": "daily routine",
}


@router.message(F.text == "📖 Чтение")
async def start_reading(
    message: Message,
    state: FSMContext,
    part_of_daily: bool = False,
    user_id_override: int | None = None,
) -> None:
    ctx = get_app_context()
    user_id = user_id_override or message.from_user.id
    profile = await ctx.users.get_profile(user_id)
    session = ctx.user_sessions.setdefault(user_id, {})
    if not part_of_daily and session.get("daily"):
        session["daily"]["active"] = False
    topic = GOAL_READING_TOPICS.get(profile.goal, "greetings and daily life")
    lesson = await ctx.deepseek.generate_reading_lesson(topic, profile.level)
    session.update(
        {
            "reading": lesson,
            "reading_id": secrets.token_hex(4),
            "q_index": 0,
            "score": 0,
        }
    )
    await state.set_state(ReadingStates.answering)
    keywords = "\n".join(
        f"• {item['word']} — {item['translation']}" for item in lesson.get("keywords", [])
    )
    text = (
        f"📖 Тема: {lesson.get('title', 'Reading')}\n\n"
        f"{lesson.get('text', '')}\n\n"
        f"🔑 Ключевые слова:\n{keywords}"
    )
    await message.answer(text)
    keywords_list = lesson.get("keywords", [])
    if keywords_list:
        first_word = keywords_list[0]["word"]
        dict_data = await ctx.dictionary.lookup(first_word)
        audio_path = await ctx.tts.get_word_audio(first_word, dict_data.get("audio_url", ""))
        if audio_path:
            await message.answer_voice(FSInputFile(audio_path))
    await _send_question(message, user_id)


@router.callback_query(ReadingStates.answering, F.data.startswith("reading:answer:"))
async def reading_answer(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = callback.from_user.id
    session = ctx.user_sessions.get(user_id, {})
    lesson = session.get("reading", {})
    questions = lesson.get("questions", [])
    q_index = int(session.get("q_index", 0))
    parts = callback.data.split(":")
    expected_token = f"{session.get('reading_id')}-{q_index}"
    if (
        len(parts) != 4
        or parts[-2] != expected_token
        or q_index >= len(questions)
    ):
        await callback.answer("Этот вопрос уже не активен", show_alert=True)
        return
    selected = int(parts[-1])
    question = questions[q_index]
    if not 0 <= selected < len(question.get("options", [])):
        await callback.answer("Некорректный вариант", show_alert=True)
        return
    correct_index = int(question.get("correct_index", 0))
    if not 0 <= correct_index < len(question.get("options", [])):
        await callback.answer("Вопрос составлен некорректно", show_alert=True)
        return
    correct = selected == correct_index
    if correct:
        session["score"] = int(session.get("score", 0)) + 1
        feedback = "✅ Верно!"
    else:
        correct_option = question["options"][correct_index]
        feedback = f"Почти! Правильно: {correct_option}\n{question.get('explanation_ru', '')}"

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
        await ctx.progress.record_lesson(user_id, "reading", lesson.get("title", "reading"), score=pct)
        await ctx.db.touch_activity(user_id)
        await ctx.db.unlock_achievement(user_id, "first_lesson")
        await state.clear()
        await callback.message.answer(
            f"📖 Урок завершён! Результат: {score}/{total} ({pct}%)\n"
            "Отличная работа!"
        )
        if await _continue_daily(callback.message, state, user_id, pct):
            return
        await callback.message.answer("Можешь выбрать следующее занятие в меню.")
        return
    await _send_question(callback.message, user_id)


async def _send_question(message: Message, user_id: int) -> None:
    ctx = get_app_context()
    session = ctx.user_sessions.get(user_id, {})
    lesson = session.get("reading", {})
    questions = lesson.get("questions", [])
    q_index = int(session.get("q_index", 0))
    if q_index >= len(questions):
        return
    question = questions[q_index]
    token = f"{session.get('reading_id')}-{q_index}"
    await message.answer(
        f"❓ {question['question']}",
        reply_markup=options_keyboard(
            question["options"],
            "reading:answer",
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

    await continue_daily(message, state, user_id, "reading", score)
    return True
