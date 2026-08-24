import secrets

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.utils.context import get_app_context
from bot.utils.exam_content import EXAMS, SECTION_LABELS
from bot.utils.keyboards import main_menu_keyboard, options_keyboard
from bot.utils.states import ExamStates

router = Router()

TARGET_BY_LEVEL = {
    "Pre-A1": "A1",
    "A1": "A2",
}


@router.message(Command("exam"))
@router.message(F.text == "🎓 Экзамен")
async def start_exam(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    profile = await ctx.users.get_profile(user_id, message.from_user.username)
    if not profile.onboarding_completed:
        await message.answer("Сначала пройди первоначальную настройку: /start")
        return

    target_level = TARGET_BY_LEVEL.get(profile.level)
    if not target_level:
        await message.answer(
            f"Твой текущий уровень — {profile.level}. "
            "Сейчас экзамены доступны до уровня A2."
        )
        return

    await state.clear()
    session = ctx.user_sessions.setdefault(user_id, {})
    daily = session.get("daily")
    if daily:
        daily["active"] = False

    exam = EXAMS[target_level]
    token = secrets.token_hex(4)
    section_scores = {
        section: {"correct": 0, "total": 0}
        for section in SECTION_LABELS
    }
    session["exam"] = {
        "active": True,
        "token": token,
        "source_level": profile.level,
        "target_level": target_level,
        "question_index": 0,
        "score": 0,
        "section_scores": section_scores,
        "last_section": None,
    }
    await state.set_state(ExamStates.answering)

    latest = await ctx.db.get_latest_exam_attempt(user_id, target_level)
    previous = ""
    if latest:
        previous = (
            f"\nПредыдущая попытка: {latest['score']}/{latest['total']} "
            f"({latest['percentage']}%).\n"
        )
    await message.answer(
        f"🎓 Экзамен {profile.level} → {target_level}\n\n"
        "15 вопросов: лексика, грамматика и чтение.\n"
        "Для повышения нужны минимум 12/15 и не менее 3/5 в каждом блоке.\n"
        "Правильные ответы будут показаны только после завершения."
        f"{previous}\nНачинаем!"
    )
    await _send_exam_question(message, user_id)


@router.callback_query(
    ExamStates.answering,
    F.data.startswith("exam:answer:"),
)
async def exam_answer(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = callback.from_user.id
    session = ctx.user_sessions.get(user_id, {})
    exam_session = session.get("exam", {})
    parts = callback.data.split(":")
    question_index = int(exam_session.get("question_index", 0))
    if (
        len(parts) != 5
        or not exam_session.get("active")
        or parts[2] != exam_session.get("token")
        or int(parts[3]) != question_index
    ):
        await callback.answer("Этот вопрос уже не активен", show_alert=True)
        return

    target_level = exam_session["target_level"]
    questions = EXAMS[target_level]["questions"]
    if question_index >= len(questions):
        await callback.answer("Экзамен уже завершён", show_alert=True)
        return

    question = questions[question_index]
    selected = int(parts[4])
    options = question["options"]
    if not 0 <= selected < len(options):
        await callback.answer("Некорректный вариант", show_alert=True)
        return

    section = question["section"]
    section_result = exam_session["section_scores"][section]
    section_result["total"] += 1
    if selected == int(question["correct_index"]):
        exam_session["score"] += 1
        section_result["correct"] += 1

    exam_session["question_index"] = question_index + 1
    await callback.message.edit_text(
        f"{callback.message.text}\n\nОтвет принят ✅",
        parse_mode=None,
    )
    await callback.answer()

    if exam_session["question_index"] >= len(questions):
        await _finish_exam(callback.message, state, user_id)
        return
    await _send_exam_question(callback.message, user_id)


async def _send_exam_question(message: Message, user_id: int) -> None:
    ctx = get_app_context()
    exam_session = ctx.user_sessions.get(user_id, {}).get("exam", {})
    target_level = exam_session.get("target_level")
    questions = EXAMS.get(target_level, {}).get("questions", [])
    index = int(exam_session.get("question_index", 0))
    if index >= len(questions):
        return

    question = questions[index]
    section = question["section"]
    if exam_session.get("last_section") != section:
        exam_session["last_section"] = section
        await message.answer(
            f"Раздел: {SECTION_LABELS[section]} "
            f"({sum(1 for item in questions if item['section'] == section)} вопросов)"
        )
    if question.get("passage"):
        await message.answer(f"📖 Текст для чтения:\n\n{question['passage']}")

    token = f"{exam_session['token']}:{index}"
    await message.answer(
        f"Вопрос {index + 1}/{len(questions)}\n{question['prompt']}",
        reply_markup=options_keyboard(
            question["options"],
            "exam:answer",
            token,
        ),
    )


async def _finish_exam(
    message: Message,
    state: FSMContext,
    user_id: int,
) -> None:
    ctx = get_app_context()
    exam_session = ctx.user_sessions[user_id]["exam"]
    questions = EXAMS[exam_session["target_level"]]["questions"]
    score = int(exam_session["score"])
    total = len(questions)
    percentage = round(score / total * 100, 1)
    section_scores = exam_session["section_scores"]
    passed = exam_passed(score, total, section_scores)
    exam_session["active"] = False
    await state.clear()

    await ctx.db.record_exam_attempt(
        user_id=user_id,
        source_level=exam_session["source_level"],
        target_level=exam_session["target_level"],
        score=score,
        total=total,
        percentage=percentage,
        passed=passed,
        section_scores=section_scores,
    )
    await ctx.progress.record_lesson(
        user_id,
        "exam",
        f"{exam_session['source_level']}_to_{exam_session['target_level']}",
        score=percentage,
    )
    await ctx.db.touch_activity(user_id)

    lines = [
        (
            f"{SECTION_LABELS[section]}: "
            f"{result['correct']}/{result['total']}"
        )
        for section, result in section_scores.items()
    ]
    breakdown = "\n".join(lines)
    if passed:
        target_level = exam_session["target_level"]
        await ctx.db.update_user(user_id, level=target_level)
        await ctx.db.unlock_achievement(
            user_id,
            f"level_{target_level.lower()}",
        )
        await message.answer(
            f"🎉 Экзамен сдан: {score}/{total} ({percentage}%)\n\n"
            f"{breakdown}\n\n"
            f"Твой новый уровень — {target_level}!",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(
        f"До повышения уровня немного не хватило: "
        f"{score}/{total} ({percentage}%).\n\n"
        f"{breakdown}\n\n"
        "Нужно 12 правильных ответов и минимум 3 в каждом блоке. "
        "Повтори слабые темы и попробуй снова командой /exam.",
        reply_markup=main_menu_keyboard(),
    )


def exam_passed(
    score: int,
    total: int,
    section_scores: dict[str, dict[str, int]],
) -> bool:
    if total <= 0 or score / total < 0.8:
        return False
    return all(
        result["total"] > 0
        and result["correct"] / result["total"] >= 0.6
        for result in section_scores.values()
    )
