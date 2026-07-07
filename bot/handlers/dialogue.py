import json

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.utils.context import AppContext
from bot.utils.keyboards import dialogue_keyboard, scenario_keyboard
from bot.utils.states import DialogueStates

router = Router()

SCENARIO_ROLES = {
    "introduction": "a new friend",
    "coffee": "a barista in a cafe",
    "ticket": "a ticket seller",
    "small_talk": "a friendly neighbor",
}


def get_ctx(message_or_query) -> AppContext:
    return message_or_query.bot["app_context"]


@router.message(F.text == "💬 Диалог")
async def start_dialogue(message: Message, state: FSMContext) -> None:
    await message.answer("Выбери сценарий диалога:", reply_markup=scenario_keyboard())


@router.callback_query(F.data.startswith("dialogue:scenario:"))
async def choose_scenario(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_ctx(callback)
    user_id = callback.from_user.id
    scenario = callback.data.split(":")[-1]
    role = SCENARIO_ROLES.get(scenario, "a friend")
    history = []
    reply = await ctx.deepseek.dialogue_reply(scenario, role, history)
    history.append({"role": "assistant", "content": reply})
    ctx.user_sessions[user_id] = {
        "dialogue_scenario": scenario,
        "dialogue_role": role,
        "dialogue_history": history,
        "dialogue_turns": 1,
    }
    await state.set_state(DialogueStates.chatting)
    await callback.message.edit_text(f"Сценарий: {scenario}")
    await callback.message.answer(reply, reply_markup=dialogue_keyboard())
    await callback.answer()


@router.callback_query(DialogueStates.chatting, F.data == "dialogue:hint")
async def dialogue_hint(callback: CallbackQuery) -> None:
    ctx = get_ctx(callback)
    user_id = callback.from_user.id
    session = ctx.user_sessions.get(user_id, {})
    history = session.get("dialogue_history", [])
    last_bot = ""
    for msg in reversed(history):
        if msg.get("role") == "assistant":
            last_bot = msg.get("content", "")
            break
    hint = await ctx.deepseek.dialogue_hint(session.get("dialogue_scenario", ""), last_bot)
    await callback.message.answer(f"💡 Подсказка:\n{hint}")
    await callback.answer()


@router.callback_query(DialogueStates.chatting, F.data == "dialogue:finish")
async def finish_dialogue(callback: CallbackQuery, state: FSMContext) -> None:
    await _complete_dialogue(callback, state)


@router.message(DialogueStates.chatting)
async def dialogue_message(message: Message, state: FSMContext) -> None:
    ctx = get_ctx(message)
    user_id = message.from_user.id
    session = ctx.user_sessions.get(user_id, {})
    history = session.get("dialogue_history", [])
    history.append({"role": "user", "content": message.text})
    turns = int(session.get("dialogue_turns", 0)) + 1
    reply = await ctx.deepseek.dialogue_reply(
        session.get("dialogue_scenario", "introduction"),
        session.get("dialogue_role", "a friend"),
        history,
    )
    history.append({"role": "assistant", "content": reply})
    session["dialogue_history"] = history
    session["dialogue_turns"] = turns
    ctx.user_sessions[user_id] = session
    await message.answer(reply, reply_markup=dialogue_keyboard())
    if turns >= 5:
        await _complete_dialogue(message, state)


async def _complete_dialogue(event, state: FSMContext) -> None:
    from aiogram.types import CallbackQuery, Message

    ctx = get_ctx(event)
    user_id = event.from_user.id
    session = ctx.user_sessions.get(user_id, {})
    history = session.get("dialogue_history", [])
    scenario = session.get("dialogue_scenario", "introduction")
    feedback = (
        "📝 Разбор диалога:\n"
        "• Ты молодец, что пробуешь говорить!\n"
        "• Старайся отвечать короткими фразами.\n"
        "• Повторяй новые слова вслух."
    )
    await ctx.db.execute(
        "INSERT INTO dialogues (user_id, scenario, messages, feedback) VALUES (?, ?, ?, ?)",
        (user_id, scenario, json.dumps(history, ensure_ascii=False), feedback),
    )
    await ctx.progress.record_lesson(user_id, "dialogue", scenario, score=100)
    await ctx.db.touch_activity(user_id)
    await ctx.db.unlock_achievement(user_id, "first_dialogue")
    await state.clear()
    if isinstance(event, CallbackQuery):
        await event.message.answer(feedback)
        await event.answer()
    elif isinstance(event, Message):
        await event.answer(feedback)
