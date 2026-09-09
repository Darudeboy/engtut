from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.utils.content import ACHIEVEMENTS
from bot.utils.context import get_app_context
from bot.utils.languages import language_label

router = Router()

@router.message(Command("stats"))
@router.message(F.text == "📊 Мой прогресс")
async def show_stats(message: Message) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    stats = await ctx.db.get_stats(user_id)
    achievements = stats.get("achievements", [])
    achievement_lines = [
        ACHIEVEMENTS.get(a["achievement_code"], a["achievement_code"]) for a in achievements
    ] or ["Пока нет — но всё впереди!"]

    text = (
        "📊 Твой прогресс\n\n"
        f"Язык: {language_label(stats['learning_language'])}\n"
        f"Уровень: {stats['level']}\n"
        f"🔥 Streak: {stats['streak_days']} дн.\n"
        f"👀 Слов встречено: {stats['words_introduced']}\n"
        f"🧠 В изучении: {stats['words_learning']}\n"
        f"✅ Освоено: {stats['words_mastered']}\n"
        f"🔁 Повторить сегодня: {stats['words_due']}\n"
        f"📚 Уроков пройдено: {stats['lessons_completed']}\n"
        f"🎯 Точность в упражнениях: {stats['accuracy']}%\n\n"
        "🏆 Достижения:\n" + "\n".join(f"• {item}" for item in achievement_lines)
    )
    await message.answer(text)

    summary_data = await ctx.progress.get_weekly_summary_data(user_id)
    if summary_data.get("weekly_modules"):
        weekly_text = await ctx.deepseek.weekly_summary(summary_data)
        await message.answer(f"📅 Недельная сводка:\n\n{weekly_text}")
