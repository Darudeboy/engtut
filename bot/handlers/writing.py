import html
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.utils.content import WRITING_STAGES
from bot.utils.context import get_app_context
from bot.utils.states import WritingStates

router = Router()
MAX_WRITING_STAGE = max(WRITING_STAGES)


@router.message(F.text == "✍️ Письмо")
async def start_writing(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    profile = await ctx.users.get_profile(user_id)
    stage = max(1, min(profile.writing_level, MAX_WRITING_STAGE))
    tasks = WRITING_STAGES[stage]
    attempt_count = await ctx.db.get_lesson_attempt_count(user_id, "writing")
    task = tasks[attempt_count % len(tasks)]
    session = ctx.user_sessions.setdefault(user_id, {})
    if session.get("daily"):
        session["daily"]["active"] = False
    if session.get("exam"):
        session["exam"]["active"] = False
    session.update(
        {
            "writing_level": stage,
            "writing_task": task,
            "learner_level": profile.level,
        }
    )
    await state.set_state(WritingStates.answering)
    format_hint = ""
    if task.get("min_words"):
        format_hint = f"\nМинимум слов: {task['min_words']}."
    await message.answer(
        f"✍️ Этап письма {stage}/{MAX_WRITING_STAGE}: {task['title']}\n\n"
        f"{task['prompt']}{format_hint}\n\n"
        "Можно ошибиться — я помогу мягко исправить."
    )


@router.message(WritingStates.answering, F.text)
async def writing_answer(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    session = ctx.user_sessions.get(user_id, {})
    task = session.get("writing_task", {})
    stage = int(session.get("writing_level", 1))
    answer = message.text.strip()
    if not task:
        await state.clear()
        await message.answer("Задание устарело. Открой раздел «Письмо» ещё раз.")
        return

    if task.get("free"):
        min_words = int(task.get("min_words", 1))
        word_count = len(re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?", answer))
        if word_count < min_words:
            result = {
                "status": "incorrect",
                "feedback": (
                    f"Ответ пока слишком короткий: {word_count} слов. "
                    f"Нужно минимум {min_words}."
                ),
                "correct_answer": task.get("reference", ""),
            }
        else:
            result = await ctx.deepseek.check_writing_task(
                prompt=task["prompt"],
                requirements=task["requirements"],
                reference=task["reference"],
                user_answer=answer,
                level=session.get("learner_level", "Pre-A1"),
                min_words=min_words,
            )
    else:
        target = task["answer"]
        result = await ctx.deepseek.check_writing_answer(
            target,
            answer,
            session.get("learner_level", "Pre-A1"),
        )
        if _normalize(answer) == _normalize(target):
            result = {
                "status": "correct",
                "feedback": "Отлично!",
                "correct_answer": target,
            }

    status = result.get("status", "incorrect")
    feedback = html.escape(str(result.get("feedback", "")))
    if status == "correct":
        score = 100
        msg = f"✅ {feedback or 'Отлично!'}"
        if stage < MAX_WRITING_STAGE:
            new_level = stage + 1
            await ctx.db.update_user(user_id, writing_level=new_level)
            msg += f"\n🎉 Открыт этап письма {new_level}!"
        else:
            msg += "\n🏅 Максимальный этап закреплён. Следующая тема будет другой."
        if stage >= 3:
            await ctx.db.unlock_achievement(user_id, "writing_level_3")
        if stage >= MAX_WRITING_STAGE:
            await ctx.db.unlock_achievement(user_id, "writing_level_8")
    elif status == "close":
        score = 70
        msg = f"🙂 {feedback or 'Смысл понятен, но ответ можно улучшить.'}"
    else:
        score = 30
        msg = f"💪 {feedback or 'Попробуй ещё немного развить ответ.'}"

    corrected = str(result.get("correct_answer", ""))
    if corrected and _normalize(corrected) != _normalize(answer):
        msg += f"\n\nВозможный вариант:\n{html.escape(corrected)}"

    await ctx.progress.record_lesson(
        user_id,
        "writing",
        task["id"],
        score=score,
    )
    await ctx.db.touch_activity(user_id)
    await state.clear()
    await message.answer(
        msg
        + "\n\nСледующий заход в «Письмо» даст новое задание текущего этапа."
    )


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9']+", " ", text.lower()).strip()
