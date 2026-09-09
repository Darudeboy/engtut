from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.services.coach import (
    build_learner_context,
    detect_intent,
    recommend_next_step,
)
from bot.utils.context import get_app_context

privacy_router = Router()
router = Router()

INTENT_LABELS = {
    "grammar": "грамматика",
    "reading": "чтение",
    "vocabulary": "слова",
    "writing": "письмо",
    "listening": "аудирование",
    "dialogue": "диалог",
    "progress": "прогресс",
    "daily": "ежедневная сессия",
    "exam": "экзамен",
}


@privacy_router.message(Command("forget"))
async def forget_tutor_history(
    message: Message,
    state: FSMContext,
) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    await ctx.db.clear_ai_history(user_id)
    ctx.user_sessions.pop(user_id, None)
    await state.clear()
    await message.answer(
        "История AI-наставника и учебных диалогов удалена. "
        "Активное упражнение остановлено.",
        parse_mode=None,
    )


@router.message(StateFilter(None), F.text)
async def tutor_message(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    profile = await ctx.users.get_profile(user_id, message.from_user.username)
    if not profile.onboarding_completed:
        await message.answer("Сначала пройди настройку: /start")
        return

    text = message.text.strip()
    if not text:
        return
    if text.startswith("/"):
        await message.answer("Неизвестная команда. Список команд: /help")
        return

    intent = detect_intent(text)
    history = await ctx.db.get_recent_tutor_messages(user_id, limit=10)
    await ctx.db.add_tutor_message(user_id, "user", text, intent)
    await ctx.db.touch_activity(user_id)

    if intent == "next":
        recommendation = await recommend_next_step(ctx.db, user_id)
        reply = f"Следующий шаг: {recommendation['text']}"
        await ctx.db.add_tutor_message(user_id, "assistant", reply, "next")
        await message.answer(reply, parse_mode=None)
        return

    if intent in INTENT_LABELS:
        await _dispatch_intent(intent, message, state)
        return

    learner_context = await build_learner_context(ctx.db, user_id)
    reply = await ctx.deepseek.coach_reply(
        learner_context,
        history,
        text[:2000],
    )
    reply = reply.strip() or (
        "Я не смог сформулировать ответ. Попробуй написать вопрос короче "
        "или попроси открыть конкретный раздел."
    )
    if len(reply) > 4000:
        reply = reply[:3997] + "..."
    await ctx.db.add_tutor_message(user_id, "assistant", reply)
    await message.answer(reply, parse_mode=None)


async def _dispatch_intent(
    intent: str,
    message: Message,
    state: FSMContext,
) -> None:
    if intent == "grammar":
        from bot.handlers.grammar import start_grammar

        await start_grammar(message, state)
    elif intent == "reading":
        from bot.handlers.reading import start_reading

        await start_reading(message, state)
    elif intent == "vocabulary":
        from bot.handlers.vocabulary import start_vocabulary

        await start_vocabulary(message, state)
    elif intent == "writing":
        from bot.handlers.writing import start_writing

        await start_writing(message, state)
    elif intent == "listening":
        from bot.handlers.listening import start_listening

        await start_listening(message, state)
    elif intent == "dialogue":
        from bot.handlers.dialogue import start_dialogue

        await start_dialogue(message, state)
    elif intent == "progress":
        from bot.handlers.progress import show_stats

        await show_stats(message)
    elif intent == "daily":
        from bot.handlers.daily import daily_session

        await daily_session(message, state)
    elif intent == "exam":
        from bot.handlers.exam import start_exam

        await start_exam(message, state)


async def send_next_step(
    message: Message,
    user_id: int,
    exclude_module: str | None = None,
) -> None:
    ctx = get_app_context()
    recommendation = await recommend_next_step(
        ctx.db,
        user_id,
        exclude_module=exclude_module,
    )
    reply = f"💡 Следующий шаг: {recommendation['text']}"
    await message.answer(reply, parse_mode=None)
