from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.utils.context import get_app_context
from bot.utils.keyboards import main_menu_keyboard

router = Router()

@router.message(F.text == "⚙️ Настройки")
async def settings(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    await _cancel_active_session(message.from_user.id, state)
    profile = await ctx.users.get_profile(message.from_user.id, message.from_user.username)
    user = await ctx.db.get_or_create_user(message.from_user.id)
    await message.answer(
        "⚙️ Настройки\n\n"
        f"Уровень: {profile.level}\n"
        f"Цель: {profile.goal or 'не указана'}\n"
        f"Напоминание: {user.get('reminder_time') or 'выключено'}\n"
        f"Цель по времени: {user.get('daily_goal_minutes', 15)} мин/день\n\n"
        "Чтобы изменить напоминание, отправь /start и пройди настройку заново."
    )


@router.message(F.text.in_({"🏠 Меню", "Меню"}))
async def show_menu(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    await _cancel_active_session(message.from_user.id, state)
    profile = await ctx.users.get_profile(message.from_user.id)
    await message.answer(
        f"👋 Главное меню\nТвой уровень: {profile.level}\n\nВыбери занятие:",
        reply_markup=main_menu_keyboard(),
    )


async def _cancel_active_session(user_id: int, state: FSMContext) -> None:
    ctx = get_app_context()
    daily = ctx.user_sessions.setdefault(user_id, {}).get("daily")
    if daily:
        daily["active"] = False
    await state.clear()
