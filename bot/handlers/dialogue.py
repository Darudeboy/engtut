import json

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.utils.context import get_app_context
from bot.utils.keyboards import dialogue_keyboard, scenario_keyboard
from bot.utils.states import DialogueStates

router = Router()

SCENARIO_ROLES = {
    "introduction": {
        "label": "Знакомство",
        "role": "a new friend",
        "criteria": ["introduce yourself", "share one personal fact", "ask one question"],
        "goals": ["hobby", "exam"],
    },
    "coffee": {
        "label": "Заказ в кафе",
        "role": "a barista in a cafe",
        "criteria": ["order a drink", "choose a size", "ask about the price"],
        "goals": ["travel"],
    },
    "ticket": {
        "label": "Покупка билета",
        "role": "a ticket seller",
        "criteria": ["name the destination", "choose a time", "ask about the price"],
        "goals": ["travel"],
    },
    "small_talk": {
        "label": "Разговор с соседом",
        "role": "a friendly neighbor",
        "criteria": ["answer two questions", "share a recent event", "ask one question"],
        "goals": ["hobby"],
    },
    "hotel": {
        "label": "Заселение в отель",
        "role": "a hotel receptionist",
        "criteria": ["say your name", "confirm the booking", "ask about breakfast"],
        "goals": ["travel"],
    },
    "directions": {
        "label": "Как пройти",
        "role": "a local person in the street",
        "criteria": ["ask for directions", "confirm one detail", "say thank you"],
        "goals": ["travel"],
    },
    "meeting": {
        "label": "Рабочая встреча",
        "role": "a colleague before a meeting",
        "criteria": ["describe your task", "mention a deadline", "offer next steps"],
        "goals": ["work"],
    },
    "support": {
        "label": "Проблема с заказом",
        "role": "a customer support agent",
        "criteria": ["describe the problem", "give an order detail", "request a solution"],
        "goals": ["work", "exam"],
    },
}


@router.message(F.text == "💬 Диалог")
async def start_dialogue(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    profile = await ctx.users.get_profile(user_id)
    if not profile.onboarding_completed:
        await message.answer("Сначала выбери язык и пройди настройку: /start")
        return
    session = ctx.user_sessions.setdefault(user_id, {})
    if session.get("daily"):
        session["daily"]["active"] = False
    if session.get("exam"):
        session["exam"]["active"] = False
    if session.get("dialogue_active"):
        session["dialogue_active"] = False
    await state.clear()
    ordered = sorted(
        SCENARIO_ROLES.items(),
        key=lambda item: profile.goal not in item[1]["goals"],
    )
    buttons = [
        (item["label"], code)
        for code, item in ordered
    ]
    await message.answer(
        f"Выбери сценарий диалога. Текущая сложность: {profile.level}.",
        reply_markup=scenario_keyboard(buttons),
    )


@router.callback_query(F.data.startswith("dialogue:scenario:"))
async def choose_scenario(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = callback.from_user.id
    scenario = callback.data.split(":")[-1]
    scenario_data = SCENARIO_ROLES.get(scenario)
    if not scenario_data:
        await callback.answer("Неизвестный сценарий", show_alert=True)
        return
    profile = await ctx.users.get_profile(user_id)
    role = scenario_data["role"]
    criteria = scenario_data["criteria"]
    history = []
    reply = await ctx.deepseek.dialogue_reply(
        scenario,
        role,
        history,
        profile.level,
        criteria,
        profile.learning_language,
    )
    history.append({"role": "assistant", "content": reply})
    session = ctx.user_sessions.setdefault(user_id, {})
    session.update(
        {
            "dialogue_active": True,
            "dialogue_scenario": scenario,
            "dialogue_role": role,
            "dialogue_criteria": criteria,
            "dialogue_level": profile.level,
            "dialogue_language": profile.learning_language,
            "dialogue_history": history,
            "dialogue_turns": 0,
        }
    )
    await state.set_state(DialogueStates.chatting)
    await callback.message.edit_text(
        f"Сценарий: {scenario_data['label']}",
        parse_mode=None,
    )
    await callback.message.answer(
        reply,
        parse_mode=None,
        reply_markup=dialogue_keyboard(),
    )
    await callback.answer()


@router.callback_query(DialogueStates.chatting, F.data == "dialogue:hint")
async def dialogue_hint(callback: CallbackQuery) -> None:
    ctx = get_app_context()
    user_id = callback.from_user.id
    session = ctx.user_sessions.get(user_id, {})
    history = session.get("dialogue_history", [])
    last_bot = ""
    for msg in reversed(history):
        if msg.get("role") == "assistant":
            last_bot = msg.get("content", "")
            break
    hint = await ctx.deepseek.dialogue_hint(
        session.get("dialogue_scenario", ""),
        last_bot,
        session.get("dialogue_level", "Pre-A1"),
        session.get("dialogue_language", "english"),
    )
    await callback.message.answer(f"💡 Подсказка:\n{hint}", parse_mode=None)
    await callback.answer()


@router.callback_query(DialogueStates.chatting, F.data == "dialogue:finish")
async def finish_dialogue(callback: CallbackQuery, state: FSMContext) -> None:
    await _complete_dialogue(callback, state)


@router.message(DialogueStates.chatting, F.text)
async def dialogue_message(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    session = ctx.user_sessions.get(user_id, {})
    history = session.get("dialogue_history", [])
    history.append({"role": "user", "content": message.text})
    turns = int(session.get("dialogue_turns", 0)) + 1
    reply = await ctx.deepseek.dialogue_reply(
        session.get("dialogue_scenario", "introduction"),
        session.get("dialogue_role", "a friend"),
        history,
        session.get("dialogue_level", "Pre-A1"),
        session.get("dialogue_criteria", []),
        session.get("dialogue_language", "english"),
    )
    history.append({"role": "assistant", "content": reply})
    session["dialogue_history"] = history
    session["dialogue_turns"] = turns
    ctx.user_sessions[user_id] = session
    await message.answer(
        reply,
        parse_mode=None,
        reply_markup=dialogue_keyboard(),
    )
    if turns >= 5:
        await _complete_dialogue(message, state)


async def _complete_dialogue(event, state: FSMContext) -> None:
    from aiogram.types import CallbackQuery, Message

    ctx = get_app_context()
    user_id = event.from_user.id
    session = ctx.user_sessions.get(user_id, {})
    history = session.get("dialogue_history", [])
    scenario = session.get("dialogue_scenario", "introduction")
    if not session.get("dialogue_active"):
        if isinstance(event, CallbackQuery):
            await event.answer("Диалог уже завершён", show_alert=True)
        return
    session["dialogue_active"] = False
    assessment = await ctx.deepseek.assess_dialogue(
        scenario,
        history,
        session.get("dialogue_level", "Pre-A1"),
        session.get("dialogue_criteria", []),
        session.get("dialogue_language", "english"),
    )
    score = int(assessment.get("score", 0))
    strengths = assessment.get("strengths", [])
    improvements = assessment.get("improvements", [])
    phrases = assessment.get("useful_phrases", [])
    feedback_parts = [
        f"📝 Разбор диалога · {score}/100",
        str(assessment.get("feedback_ru", "")),
    ]
    if strengths:
        feedback_parts.append("Получилось:\n• " + "\n• ".join(map(str, strengths[:2])))
    if improvements:
        feedback_parts.append(
            "Следующий шаг:\n• " + "\n• ".join(map(str, improvements[:2]))
        )
    if phrases:
        feedback_parts.append(
            "Полезные фразы:\n• " + "\n• ".join(map(str, phrases[:3]))
        )
    feedback = "\n\n".join(part for part in feedback_parts if part)
    await ctx.db.execute(
        """
        INSERT INTO dialogues (user_id, language, scenario, messages, feedback)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            session.get("dialogue_language", "english"),
            scenario,
            json.dumps(history, ensure_ascii=False),
            feedback,
        ),
    )
    await ctx.progress.record_lesson(
        user_id,
        "dialogue",
        scenario,
        score=score,
        language=session.get("dialogue_language", "english"),
    )
    await ctx.db.touch_activity(user_id)
    await ctx.db.unlock_achievement(user_id, "first_dialogue")
    await state.clear()
    if isinstance(event, CallbackQuery):
        await event.message.answer(feedback, parse_mode=None)
        await event.answer()
        followup_message = event.message
    elif isinstance(event, Message):
        await event.answer(feedback, parse_mode=None)
        followup_message = event
    else:
        return
    from bot.handlers.tutor import send_next_step

    await send_next_step(
        followup_message,
        user_id,
        exclude_module="dialogue",
    )
