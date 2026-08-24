from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.utils.context import get_app_context
from bot.utils.states import DailyStates

router = Router()

@router.message(Command("daily"))
async def daily_session(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    profile = await ctx.users.get_profile(user_id, message.from_user.username)

    if not profile.onboarding_completed:
        await message.answer("Сначала пройди онбординг: /start")
        return

    await state.set_state(DailyStates.in_session)
    await message.answer(
        "🌟 Задание дня (10–15 минут)\n\n"
        "1️⃣ Новые слова\n"
        "2️⃣ Повторение\n"
        "3️⃣ Чтение\n"
        "4️⃣ Грамматика\n"
        "5️⃣ Обратная связь\n\n"
        "Начинаем с блока «Слова»..."
    )

    from bot.handlers.vocabulary import start_vocabulary

    await start_vocabulary(message, state)
    await message.answer("Далее — 📖 Чтение. Нажми кнопку в меню или продолжай по плану.")

    streak = await ctx.db.touch_activity(user_id)
    if streak >= 7:
        await ctx.db.unlock_achievement(user_id, "seven_day_streak")

    stats = await ctx.db.get_stats(user_id)
    await message.answer(
        "✅ Ежедневная сессия начата!\n"
        f"🔥 Streak: {streak} дн.\n"
        f"🔤 Слов: {stats['words_learned']} | 📚 Уроков: {stats['lessons_completed']}"
    )
    await state.clear()
