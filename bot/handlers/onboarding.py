from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.utils.content import LEVEL_QUESTIONS
from bot.utils.context import get_app_context
from bot.utils.keyboards import (
    goal_keyboard,
    language_keyboard,
    main_menu_keyboard,
    options_keyboard,
    reminder_keyboard,
)
from bot.utils.languages import ITALIAN_LEVEL_QUESTIONS, language_label
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
            f"С возвращением! 👋\n"
            f"Язык: {language_label(profile.learning_language)}\n"
            f"Твой уровень: {profile.level}\n\nВыбери занятие:",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.set_state(OnboardingStates.language)
    await message.answer(
        "👋 Привет! Я твой AI-тьютор.\n\n"
        "Сначала выбери язык, который хочешь изучать:",
        reply_markup=language_keyboard(
            profile.learning_language,
            "onboard:language",
        ),
    )


@router.callback_query(
    OnboardingStates.language,
    F.data.startswith("onboard:language:"),
)
async def choose_learning_language(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    ctx = get_app_context()
    language = callback.data.removeprefix("onboard:language:")
    if language not in {"english", "italian"}:
        await callback.answer("Этот язык пока недоступен", show_alert=True)
        return
    await ctx.db.set_learning_language(callback.from_user.id, language)
    await state.set_state(OnboardingStates.level_test)
    await state.update_data(
        level_q=0,
        level_score=0,
        learning_language=language,
    )
    await callback.message.edit_text(
        f"Выбран язык: {language_label(language)} ✅"
    )
    await callback.message.answer(
        "Мы будем учиться маленькими шагами: сначала понимание, потом выбор, "
        "потом короткие ответы и диалоги.\n\n"
        "Сначала — 5 простых вопросов без письма. Готов(а)?"
    )
    questions = (
        ITALIAN_LEVEL_QUESTIONS
        if language == "italian"
        else LEVEL_QUESTIONS
    )
    await _send_level_question(callback.message, 0, questions)
    await callback.answer()


@router.callback_query(OnboardingStates.level_test, F.data.startswith("onboard:level:"))
async def level_answer(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    data = await state.get_data()
    q_index = int(data.get("level_q", 0))
    score = int(data.get("level_score", 0))
    questions = (
        ITALIAN_LEVEL_QUESTIONS
        if data.get("learning_language") == "italian"
        else LEVEL_QUESTIONS
    )
    selected = int(callback.data.split(":")[-1])
    question = questions[q_index]
    if selected == question["correct_index"]:
        score += 1

    q_index += 1
    if q_index >= len(questions):
        level = "Pre-A1" if score <= 2 else "A1"
        await state.update_data(level=level, level_score=score)
        await state.set_state(OnboardingStates.goal)
        await callback.message.edit_text(
            f"Отлично! Твой уровень: {level} ({score}/{len(questions)})\n\n"
            "Для чего ты изучаешь язык?"
        )
        await callback.message.answer("Выбери цель:", reply_markup=goal_keyboard())
        await callback.answer()
        return

    await state.update_data(level_q=q_index, level_score=score)
    await callback.message.edit_text(f"Верно!" if selected == question["correct_index"] else "Ничего страшного, учимся дальше!")
    await _send_level_question(callback.message, q_index, questions)
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
    reminder = callback.data.removeprefix("onboard:reminder:")
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


async def _send_level_question(
    message: Message,
    index: int,
    questions: list[dict] | None = None,
) -> None:
    questions = questions or LEVEL_QUESTIONS
    question = questions[index]
    text = f"Вопрос {index + 1}/{len(questions)}:\n{question['question']}"
    await message.answer(text, reply_markup=options_keyboard(question["options"], "onboard:level"))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📚 Команды:\n"
        "/start — начать или вернуться в меню\n"
        "/daily — задание дня (10–15 минут)\n"
        "/exam — экзамен для повышения уровня\n"
        "/stats — твой прогресс\n"
        "/whatsnew — что нового в боте\n"
        "/forget — удалить историю AI-наставника\n"
        "/help — эта справка\n\n"
        "Вне упражнения можешь писать обычным текстом: задать вопрос, "
        "потренировать выбранный язык или попросить «давай грамматику».\n\n"
        "Модули в меню:\n"
        "📖 Чтение · 🔤 Слова · 📚 Грамматика\n"
        "✍️ Письмо · 💬 Диалог · 🎧 Аудирование · 🎓 Экзамен"
    )
