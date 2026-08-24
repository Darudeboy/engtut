from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.utils.content import LEVEL_QUESTIONS
from bot.utils.context import get_app_context
from bot.utils.keyboards import goal_keyboard, main_menu_keyboard, options_keyboard, reminder_keyboard
from bot.utils.states import OnboardingStates

router = Router()

GOAL_LABELS = {
    "travel": "Путешествия",
    "work": "Работа",
    "hobby": "Хобби",
    "exam": "Экзамен",
}

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    profile = await ctx.users.get_profile(message.from_user.id, message.from_user.username)
    if profile.onboarding_completed:
        await message.answer(
            f"С возвращением! 👋\nТвой уровень: {profile.level}\n\nВыбери занятие:",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.set_state(OnboardingStates.level_test)
    await state.update_data(level_q=0, level_score=0)
    await message.answer(
        "👋 Привет! Я твой AI-тьютор по английскому.\n\n"
        "Мы будем учиться маленькими шагами: сначала понимание, потом выбор, "
        "потом короткие ответы и диалоги.\n\n"
        "Сначала — 5 простых вопросов без письма. Готов(а)?"
    )
    await _send_level_question(message, 0)


@router.callback_query(OnboardingStates.level_test, F.data.startswith("onboard:level:"))
async def level_answer(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    data = await state.get_data()
    q_index = int(data.get("level_q", 0))
    score = int(data.get("level_score", 0))
    selected = int(callback.data.split(":")[-1])
    question = LEVEL_QUESTIONS[q_index]
    if selected == question["correct_index"]:
        score += 1

    q_index += 1
    if q_index >= len(LEVEL_QUESTIONS):
        level = "Pre-A1" if score <= 2 else "A1"
        await state.update_data(level=level, level_score=score)
        await state.set_state(OnboardingStates.goal)
        await callback.message.edit_text(
            f"Отлично! Твой уровень: {level} ({score}/{len(LEVEL_QUESTIONS)})\n\n"
            "Зачем тебе английский?"
        )
        await callback.message.answer("Выбери цель:", reply_markup=goal_keyboard())
        await callback.answer()
        return

    await state.update_data(level_q=q_index, level_score=score)
    await callback.message.edit_text(f"Верно!" if selected == question["correct_index"] else "Ничего страшного, учимся дальше!")
    await _send_level_question(callback.message, q_index)
    await callback.answer()


@router.callback_query(OnboardingStates.goal, F.data.startswith("onboard:goal:"))
async def choose_goal(callback: CallbackQuery, state: FSMContext) -> None:
    goal = callback.data.split(":")[-1]
    await state.update_data(goal=goal)
    await state.set_state(OnboardingStates.reminder)
    await callback.message.edit_text(
        f"Цель: {GOAL_LABELS.get(goal, goal)} ✅\n\n"
        "Когда напоминать о занятиях?"
    )
    await callback.message.answer("Выбери время:", reply_markup=reminder_keyboard())
    await callback.answer()


@router.callback_query(OnboardingStates.reminder, F.data.startswith("onboard:reminder:"))
async def choose_reminder(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    reminder = callback.data.split(":")[-1]
    reminder_time = None if reminder == "none" else reminder
    data = await state.get_data()
    user_id = callback.from_user.id
    await ctx.users.complete_onboarding(
        user_id=user_id,
        level=data.get("level", "Pre-A1"),
        goal=data.get("goal", "hobby"),
        reminder_time=reminder_time,
    )
    await ctx.db.touch_activity(user_id)
    await ctx.db.unlock_achievement(user_id, "first_lesson")
    await state.clear()
    await callback.message.edit_text("Настройка завершена! 🎉")
    await callback.message.answer(
        "Вот твоё первое микро-занятие — короткий текст для чтения.\n"
        "Нажми 📖 Чтение в меню или /daily для ежедневной сессии.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


async def _send_level_question(message: Message, index: int) -> None:
    question = LEVEL_QUESTIONS[index]
    text = f"Вопрос {index + 1}/{len(LEVEL_QUESTIONS)}:\n{question['question']}"
    await message.answer(text, reply_markup=options_keyboard(question["options"], "onboard:level"))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📚 Команды:\n"
        "/start — начать или вернуться в меню\n"
        "/daily — задание дня (10–15 минут)\n"
        "/exam — экзамен для повышения уровня\n"
        "/stats — твой прогресс\n"
        "/help — эта справка\n\n"
        "Модули в меню:\n"
        "📖 Чтение · 🔤 Слова · 📚 Грамматика\n"
        "✍️ Письмо · 💬 Диалог · 🎧 Аудирование · 🎓 Экзамен"
    )
