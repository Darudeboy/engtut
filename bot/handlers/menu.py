from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.utils.context import get_app_context
from bot.utils.keyboards import (
    language_keyboard,
    main_menu_keyboard,
    reminder_keyboard,
    settings_keyboard,
)
from bot.utils.languages import language_label

router = Router()

@router.message(F.text == "⚙️ Настройки")
async def settings(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    await _cancel_active_session(message.from_user.id, state)
    profile = await ctx.users.get_profile(message.from_user.id, message.from_user.username)
    user = await ctx.db.get_or_create_user(message.from_user.id)
    await message.answer(
        "⚙️ Настройки\n\n"
        f"Язык обучения: {language_label(profile.learning_language)}\n"
        f"Уровень: {profile.level}\n"
        f"Цель: {profile.goal or 'не указана'}\n"
        f"Напоминание: {user.get('reminder_time') or 'выключено'}\n"
        f"Цель по времени: {user.get('daily_goal_minutes', 15)} мин/день",
        reply_markup=settings_keyboard(),
    )


@router.message(F.text == "🌐 Язык")
async def select_language(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    await _cancel_active_session(message.from_user.id, state)
    profile = await ctx.users.get_profile(
        message.from_user.id,
        message.from_user.username,
    )
    await message.answer(
        "🌐 Какой язык будем изучать?\n\n"
        "У каждого языка отдельные уровень, слова, уроки и история наставника.",
        reply_markup=language_keyboard(profile.learning_language),
    )


@router.callback_query(F.data.startswith("language:select:"))
async def save_language(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    language = callback.data.removeprefix("language:select:")
    if language not in {"english", "italian"}:
        await callback.answer("Этот язык пока недоступен", show_alert=True)
        return
    await ctx.db.set_learning_language(callback.from_user.id, language)
    ctx.user_sessions.pop(callback.from_user.id, None)
    await state.clear()
    profile = await ctx.users.get_profile(callback.from_user.id)
    await callback.message.edit_text(
        f"✅ Выбран язык: {language_label(language)}\n"
        f"Текущий уровень этой программы: {profile.level}"
    )
    await callback.message.answer(
        "Выбери занятие:",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "settings:reminder")
async def choose_reminder_time(callback: CallbackQuery) -> None:
    ctx = get_app_context()
    await callback.message.edit_text(
        "⏰ Когда ежедневно напоминать о занятиях?\n\n"
        f"Время указано для часового пояса {ctx.settings.app_timezone}.",
        reply_markup=reminder_keyboard("settings:reminder"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings:reminder:"))
async def save_reminder_time(callback: CallbackQuery) -> None:
    ctx = get_app_context()
    value = callback.data.removeprefix("settings:reminder:")
    reminder_time = None if value == "none" else value
    await ctx.db.update_user(
        callback.from_user.id,
        reminder_time=reminder_time,
    )
    if reminder_time:
        text = (
            "✅ Напоминание включено.\n\n"
            f"Каждый день в {reminder_time} я напишу: «Пора заниматься!»"
        )
    else:
        text = "🔕 Напоминания выключены."
    await callback.message.edit_text(text)
    await callback.answer()


@router.message(F.text.in_({"🏠 Меню", "Меню"}))
async def show_menu(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    await _cancel_active_session(message.from_user.id, state)
    profile = await ctx.users.get_profile(message.from_user.id)
    await message.answer(
        f"👋 Главное меню\n"
        f"Язык: {language_label(profile.learning_language)}\n"
        f"Твой уровень: {profile.level}\n\nВыбери занятие:",
        reply_markup=main_menu_keyboard(),
    )


async def _cancel_active_session(user_id: int, state: FSMContext) -> None:
    ctx = get_app_context()
    daily = ctx.user_sessions.setdefault(user_id, {}).get("daily")
    if daily:
        daily["active"] = False
    await state.clear()
