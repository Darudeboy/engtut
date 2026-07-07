from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.utils.content import WRITING_LEVELS
from bot.utils.context import AppContext
from bot.utils.states import WritingStates

router = Router()


def get_ctx(message: Message) -> AppContext:
    return message.bot["app_context"]


@router.message(F.text == "✍️ Письмо")
async def start_writing(message: Message, state: FSMContext) -> None:
    ctx = get_ctx(message)
    user_id = message.from_user.id
    profile = await ctx.users.get_profile(user_id)
    level = min(profile.writing_level, 5)
    task = WRITING_LEVELS[level]
    ctx.user_sessions[user_id] = {"writing_level": level, "task": task}
    await state.set_state(WritingStates.answering)
    await message.answer(
        f"✍️ Уровень {level}: {task['title']}\n\n{task['prompt']}\n\n"
        "Можно ошибиться — я помогу мягко исправить."
    )


@router.message(WritingStates.answering)
async def writing_answer(message: Message, state: FSMContext) -> None:
    ctx = get_ctx(message)
    user_id = message.from_user.id
    session = ctx.user_sessions.get(user_id, {})
    task = session.get("task", {})
    level = int(session.get("writing_level", 1))
    answer = message.text.strip()
    target = task.get("answer", "")

    if task.get("free"):
        result = await ctx.deepseek.check_writing_answer(target, answer)
    else:
        result = await ctx.deepseek.check_writing_answer(target, answer)
        if answer.lower() == target.lower():
            result = {"status": "correct", "feedback": "Отлично!", "correct_answer": target}

    status = result.get("status", "incorrect")
    feedback = result.get("feedback", "")
    if status == "correct":
        score = 100
        msg = f"✅ {feedback or 'Отлично!'}"
        if level < 5:
            new_level = level + 1
            await ctx.db.update_user(user_id, writing_level=new_level)
            msg += f"\n🎉 Открыт уровень письма {new_level}!"
        if level >= 3:
            await ctx.db.unlock_achievement(user_id, "writing_level_3")
    elif status == "close":
        score = 70
        msg = f"🙂 {feedback}"
    else:
        score = 30
        msg = f"💪 {feedback}"

    await ctx.progress.record_lesson(user_id, "writing", f"level_{level}", score=score)
    await ctx.db.touch_activity(user_id)
    await state.clear()
    await message.answer(msg + "\n\nВыбери следующее занятие в меню.")
