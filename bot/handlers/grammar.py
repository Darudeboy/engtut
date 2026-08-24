from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.utils.content import GRAMMAR_TOPICS
from bot.utils.context import get_app_context
from bot.utils.keyboards import options_keyboard
from bot.utils.states import GrammarStates

router = Router()

@router.message(F.text == "📚 Грамматика")
async def start_grammar(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    user = await ctx.db.get_or_create_user(user_id)
    topic_index = int(user.get("grammar_topic_index") or 0) % len(GRAMMAR_TOPICS)
    topic = GRAMMAR_TOPICS[topic_index]
    cache_key = f"grammar:{topic}"
    lesson = await ctx.db.get_cache(cache_key)
    if not lesson:
        lesson = await ctx.deepseek.generate_grammar_exercise(topic)
        await ctx.db.set_cache(cache_key, lesson)

    ctx.user_sessions[user_id] = {
        "grammar": lesson,
        "topic": topic,
        "topic_index": topic_index,
        "q_index": 0,
        "score": 0,
        "mistakes": 0,
    }
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
    selected = int(callback.data.split(":")[-1])
    question = questions[q_index]
    correct_idx = question.get("correct_index", 0)
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
    await callback.message.edit_text(f"{callback.message.text}\n\n{feedback}")
    await callback.answer()

    if q_index >= len(questions):
        score = session.get("score", 0)
        total = len(questions) or 1
        pct = round(score / total * 100, 1)
        topic_index = int(session.get("topic_index", 0))
        if session.get("mistakes", 0) == 0:
            topic_index = (topic_index + 1) % len(GRAMMAR_TOPICS)
            await ctx.db.update_user(user_id, grammar_topic_index=topic_index)
        await ctx.progress.record_lesson(user_id, "grammar", session.get("topic", "grammar"), score=pct)
        await ctx.db.touch_activity(user_id)
        await state.clear()
        await callback.message.answer(f"📚 Грамматика завершена: {score}/{total} ({pct}%)")
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
    await message.answer(
        f"✏️ {question['prompt']}",
        reply_markup=options_keyboard(question["options"], "grammar:answer"),
    )
