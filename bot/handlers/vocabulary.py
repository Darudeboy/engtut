import json
import random
from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.config import WORDLISTS_DIR
from bot.utils.context import get_app_context
from bot.utils.keyboards import review_quality_keyboard
from bot.utils.states import VocabularyStates

router = Router()

def _load_wordlists() -> list[dict]:
    words = []
    for path in WORDLISTS_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        theme = data.get("theme", path.stem)
        for item in data.get("words", []):
            words.append({**item, "theme": theme})
    return words


@router.message(F.text == "🔤 Слова")
async def start_vocabulary(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    due = await ctx.vocabulary.get_due_reviews(user_id, limit=ctx.settings.review_words_per_session)
    if due:
        await state.set_state(VocabularyStates.reviewing)
        ctx.user_sessions[user_id] = {"vocab_reviews": due, "review_index": 0}
        await message.answer(f"🔁 Повторение: {len(due)} слов")
        await _send_review_card(message, user_id)
        return

    learned_today = await ctx.vocabulary.get_words_learned_today(user_id)
    remaining = max(0, ctx.settings.new_words_per_day - learned_today)
    if remaining == 0:
        await message.answer(
            f"Сегодня ты уже выучил(а) {learned_today} новых слов. "
            "Возвращайся завтра или выбери другое занятие!"
        )
        return

    all_words = _load_wordlists()
    random.shuffle(all_words)
    new_words = []
    for item in all_words:
        if await ctx.vocabulary.user_has_word(user_id, item["word"]):
            continue
        new_words.append(item)
        if len(new_words) >= remaining:
            break

    if not new_words:
        await message.answer("Ты уже знаешь все слова из базовых наборов! 🎉")
        return

    await message.answer(f"🔤 Новые слова сегодня: {len(new_words)}")
    for item in new_words:
        dict_data = await ctx.dictionary.lookup(item["word"])
        examples = await ctx.tatoeba.get_examples(item["word"], limit=1)
        example_en = examples[0]["en"] if examples else dict_data.get("example", "")
        example_ru = examples[0]["ru"] if examples else ""
        await ctx.vocabulary.add_word(
            user_id=user_id,
            word=item["word"],
            translation=item["translation"],
            theme=item.get("theme", "general"),
            transcription=dict_data.get("phonetic", ""),
            example_en=example_en,
            example_ru=example_ru,
        )
        text = (
            f"📝 *{item['word']}* [{dict_data.get('phonetic', '')}]\n"
            f"Перевод: {item['translation']}\n"
        )
        if example_en:
            text += f"Пример: {example_en}"
            if example_ru:
                text += f" ({example_ru})"
        await message.answer(text, parse_mode="Markdown")
        audio_path = await ctx.tts.get_word_audio(item["word"], dict_data.get("audio_url", ""))
        if audio_path:
            await message.answer_voice(FSInputFile(audio_path))

    count = await ctx.vocabulary.get_words_count(user_id)
    if count >= 10:
        await ctx.db.unlock_achievement(user_id, "ten_words")
    await ctx.progress.record_lesson(user_id, "vocabulary", "new_words", score=100)
    await ctx.db.touch_activity(user_id)
    await message.answer(f"Готово! Всего слов в словаре: {count}")


@router.callback_query(VocabularyStates.reviewing, F.data.startswith("vocab:review:"))
async def review_word(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = callback.from_user.id
    _, _, word_id, quality = callback.data.split(":")
    await ctx.vocabulary.review_word(user_id, int(word_id), int(quality))
    session = ctx.user_sessions.get(user_id, {})
    idx = int(session.get("review_index", 0)) + 1
    reviews = session.get("vocab_reviews", [])
    session["review_index"] = idx
    ctx.user_sessions[user_id] = session
    await callback.message.edit_text(f"{callback.message.text}\n\nЗаписано ✅")
    await callback.answer()
    if idx >= len(reviews):
        await state.clear()
        await ctx.progress.record_lesson(user_id, "vocabulary", "review", score=100)
        await callback.message.answer("🔁 Повторение завершено!")
        return
    await _send_review_card(callback.message, user_id)


async def _send_review_card(message: Message, user_id: int) -> None:
    ctx = get_app_context()
    session = ctx.user_sessions.get(user_id, {})
    reviews = session.get("vocab_reviews", [])
    idx = int(session.get("review_index", 0))
    if idx >= len(reviews):
        return
    card = reviews[idx]
    text = (
        f"Карточка {idx + 1}/{len(reviews)}\n"
        f"Слово: *{card['word']}*\n"
        f"Перевод: {card['translation']}"
    )
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=review_quality_keyboard(card["id"]),
    )
