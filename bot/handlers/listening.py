from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.utils.content import LISTENING_RESOURCES
from bot.utils.context import get_app_context
from bot.utils.keyboards import options_keyboard
from bot.utils.states import ListeningStates

router = Router()

LISTENING_QUESTIONS = [
    {
        "question": "What is this lesson about?",
        "options": ["Travel", "Daily life", "Sports"],
        "correct_index": 1,
    },
    {
        "question": "How long is a typical BBC 6 Minute episode?",
        "options": ["3 minutes", "6 minutes", "15 minutes"],
        "correct_index": 1,
    },
]

@router.message(F.text == "🎧 Аудирование")
async def start_listening(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    resource = LISTENING_RESOURCES[0]
    text = (
        "🎧 Аудирование (опциональный модуль)\n\n"
        f"📻 {resource['title']}\n"
        f"{resource['description']}\n"
        f"🔗 {resource['url']}\n\n"
        "Послушай 2–3 минуты, затем ответь на вопросы."
    )
    await message.answer(text)
    for item in LISTENING_RESOURCES[1:]:
        await message.answer(f"📻 {item['title']}\n{item['url']}")

    ctx.user_sessions[user_id] = {"listening_q": 0, "listening_score": 0}
    await state.set_state(ListeningStates.answering)
    await _send_listening_question(message, user_id)


@router.callback_query(ListeningStates.answering, F.data.startswith("listening:answer:"))
async def listening_answer(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = callback.from_user.id
    session = ctx.user_sessions.get(user_id, {})
    q_index = int(session.get("listening_q", 0))
    selected = int(callback.data.split(":")[-1])
    question = LISTENING_QUESTIONS[q_index]
    if selected == question["correct_index"]:
        session["listening_score"] = int(session.get("listening_score", 0)) + 1
        feedback = "✅ Верно!"
    else:
        feedback = f"Правильно: {question['options'][question['correct_index']]}"

    q_index += 1
    session["listening_q"] = q_index
    ctx.user_sessions[user_id] = session
    await callback.message.edit_text(f"{callback.message.text}\n\n{feedback}")
    await callback.answer()

    if q_index >= len(LISTENING_QUESTIONS):
        score = session.get("listening_score", 0)
        total = len(LISTENING_QUESTIONS)
        pct = round(score / total * 100, 1)
        await ctx.progress.record_lesson(user_id, "listening", "resources", score=pct)
        await ctx.db.touch_activity(user_id)
        await state.clear()
        await callback.message.answer(f"🎧 Аудирование завершено: {score}/{total}")
        return
    await _send_listening_question(callback.message, user_id)


async def _send_listening_question(message: Message, user_id: int) -> None:
    ctx = get_app_context()
    session = ctx.user_sessions.get(user_id, {})
    q_index = int(session.get("listening_q", 0))
    question = LISTENING_QUESTIONS[q_index]
    await message.answer(
        f"❓ {question['question']}",
        reply_markup=options_keyboard(question["options"], "listening:answer"),
    )
