from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.utils.context import AppContext
from bot.utils.keyboards import options_keyboard, skip_keyboard
from bot.utils.states import ReadingStates

router = Router()


def get_ctx(message_or_query) -> AppContext:
    return message_or_query.bot["app_context"]


@router.message(F.text == "📖 Чтение")
async def start_reading(message: Message, state: FSMContext) -> None:
    ctx = get_ctx(message)
    user_id = message.from_user.id
    profile = await ctx.users.get_profile(user_id)
    lesson = await ctx.deepseek.generate_reading_lesson("greetings", profile.level)
    ctx.user_sessions[user_id] = {"reading": lesson, "q_index": 0, "score": 0}
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
    ctx = get_ctx(callback)
    user_id = callback.from_user.id
    session = ctx.user_sessions.get(user_id, {})
    lesson = session.get("reading", {})
    questions = lesson.get("questions", [])
    q_index = int(session.get("q_index", 0))
    selected = int(callback.data.split(":")[-1])
    question = questions[q_index]
    correct = selected == question.get("correct_index", 0)
    if correct:
        session["score"] = int(session.get("score", 0)) + 1
        feedback = "✅ Верно!"
    else:
        correct_option = question["options"][question.get("correct_index", 0)]
        feedback = f"Почти! Правильно: {correct_option}\n{question.get('explanation_ru', '')}"

    q_index += 1
    session["q_index"] = q_index
    ctx.user_sessions[user_id] = session
    await callback.message.edit_text(f"{callback.message.text}\n\n{feedback}")
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
            "Отличная работа! Можешь выбрать следующее занятие в меню."
        )
        return
    await _send_question(callback.message, user_id)


async def _send_question(message: Message, user_id: int) -> None:
    ctx = get_ctx(message)
    session = ctx.user_sessions.get(user_id, {})
    lesson = session.get("reading", {})
    questions = lesson.get("questions", [])
    q_index = int(session.get("q_index", 0))
    if q_index >= len(questions):
        return
    question = questions[q_index]
    await message.answer(
        f"❓ {question['question']}",
        reply_markup=options_keyboard(question["options"], "reading:answer"),
    )
