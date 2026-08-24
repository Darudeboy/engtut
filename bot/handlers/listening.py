import secrets

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.utils.content import LISTENING_RESOURCES
from bot.utils.context import get_app_context
from bot.utils.keyboards import options_keyboard
from bot.utils.states import ListeningStates

router = Router()

GOAL_LISTENING_TOPICS = {
    "travel": "travel and transport",
    "work": "work and office life",
    "hobby": "free time and hobbies",
    "exam": "everyday situations",
}


@router.message(F.text == "🎧 Аудирование")
async def start_listening(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    profile = await ctx.users.get_profile(user_id)
    attempts = await ctx.db.get_lesson_attempt_count(user_id, "listening")
    variant = attempts % 6
    topic = GOAL_LISTENING_TOPICS.get(profile.goal, "daily life")
    cache_key = f"listening:{profile.level}:{topic}:{variant}"
    lesson = await ctx.db.get_cache(cache_key)
    if not lesson:
        lesson = await ctx.deepseek.generate_listening_lesson(
            topic,
            profile.level,
            variant,
        )
        await ctx.db.set_cache(cache_key, lesson)

    audio_path = await ctx.tts.synthesize(lesson["transcript"])
    if not audio_path:
        await state.clear()
        await message.answer(
            "Не удалось подготовить аудио. Попробуй открыть аудирование чуть позже."
        )
        return

    session = ctx.user_sessions.setdefault(user_id, {})
    if session.get("daily"):
        session["daily"]["active"] = False
    if session.get("exam"):
        session["exam"]["active"] = False
    session.update(
        {
            "listening_lesson": lesson,
            "listening_id": secrets.token_hex(4),
            "listening_q": 0,
            "listening_score": 0,
            "listening_variant": variant,
        }
    )
    await state.set_state(ListeningStates.answering)
    await message.answer(
        f"🎧 {lesson.get('title', 'Аудирование')}\n\n"
        "Прослушай запись. Текст появится только после ответов. "
        "При необходимости можно включить запись ещё раз.",
        parse_mode=None,
    )
    try:
        await message.answer_voice(FSInputFile(audio_path))
    finally:
        audio_path.unlink(missing_ok=True)
    await _send_listening_question(message, user_id)


@router.callback_query(ListeningStates.answering, F.data.startswith("listening:answer:"))
async def listening_answer(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = callback.from_user.id
    session = ctx.user_sessions.get(user_id, {})
    lesson = session.get("listening_lesson", {})
    questions = lesson.get("questions", [])
    q_index = int(session.get("listening_q", 0))
    parts = callback.data.split(":")
    expected_token = f"{session.get('listening_id')}:{q_index}"
    if (
        len(parts) != 5
        or f"{parts[2]}:{parts[3]}" != expected_token
        or q_index >= len(questions)
    ):
        await callback.answer("Этот вопрос уже не активен", show_alert=True)
        return
    selected = int(parts[-1])
    question = questions[q_index]
    options = question.get("options", [])
    correct_index = int(question.get("correct_index", 0))
    if (
        not 0 <= selected < len(options)
        or not 0 <= correct_index < len(options)
    ):
        await callback.answer("Вопрос составлен некорректно", show_alert=True)
        return
    if selected == correct_index:
        session["listening_score"] = int(session.get("listening_score", 0)) + 1
        feedback = "✅ Верно!"
    else:
        feedback = f"Правильно: {options[correct_index]}"
    explanation = question.get("explanation_ru", "")
    if explanation:
        feedback += f"\n{explanation}"

    q_index += 1
    session["listening_q"] = q_index
    ctx.user_sessions[user_id] = session
    await callback.message.edit_text(
        f"{callback.message.text}\n\n{feedback}",
        parse_mode=None,
    )
    await callback.answer()

    if q_index >= len(questions):
        score = session.get("listening_score", 0)
        total = len(questions) or 1
        pct = round(score / total * 100, 1)
        await ctx.progress.record_lesson(
            user_id,
            "listening",
            f"{lesson.get('title', 'listening')}:{session.get('listening_variant', 0)}",
            score=pct,
        )
        await ctx.db.touch_activity(user_id)
        await state.clear()
        resource = LISTENING_RESOURCES[0]
        await callback.message.answer(
            f"🎧 Аудирование завершено: {score}/{total} ({pct}%)\n\n"
            f"Текст записи:\n{lesson.get('transcript', '')}\n\n"
            f"Для дополнительной практики: {resource['title']}\n{resource['url']}",
            parse_mode=None,
        )
        return
    await _send_listening_question(callback.message, user_id)


async def _send_listening_question(message: Message, user_id: int) -> None:
    ctx = get_app_context()
    session = ctx.user_sessions.get(user_id, {})
    lesson = session.get("listening_lesson", {})
    questions = lesson.get("questions", [])
    q_index = int(session.get("listening_q", 0))
    if q_index >= len(questions):
        return
    question = questions[q_index]
    token = f"{session.get('listening_id')}:{q_index}"
    await message.answer(
        f"❓ Вопрос {q_index + 1}/{len(questions)}\n{question['question']}",
        parse_mode=None,
        reply_markup=options_keyboard(
            question["options"],
            "listening:answer",
            token,
        ),
    )
