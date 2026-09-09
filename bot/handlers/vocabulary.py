import html
import json
import random

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.config import WORDLISTS_DIR
from bot.utils.context import get_app_context
from bot.utils.keyboards import (
    review_quality_keyboard,
    review_reveal_keyboard,
    vocabulary_menu_keyboard,
    vocabulary_theme_keyboard,
)
from bot.utils.languages import language_info
from bot.utils.states import VocabularyStates

router = Router()

THEME_LABELS = {
    "basics": "Основы",
    "numbers": "Числа",
    "days": "Дни недели",
    "food": "Еда",
    "family": "Семья",
    "home": "Дом",
    "travel": "Путешествия",
    "work": "Работа",
    "verbs": "Основные глаголы",
    "adjectives": "Прилагательные",
    "shopping": "Покупки",
    "weather": "Погода",
    "body": "Тело и здоровье",
    "clothes": "Одежда",
    "hobbies": "Хобби",
    "city": "Город",
}


def _load_wordlists(
    theme_filter: str | None = None,
    language: str = "english",
) -> list[dict]:
    words = []
    directory = (
        WORDLISTS_DIR / "italian"
        if language == "italian"
        else WORDLISTS_DIR
    )
    for path in directory.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        theme = data.get("theme", path.stem)
        for item in data.get("words", []):
            item_theme = item.get("theme", theme)
            if theme_filter and item_theme != theme_filter:
                continue
            words.append({**item, "theme": item_theme})
    return words


def _available_themes(language: str = "english") -> list[tuple[str, str]]:
    themes = sorted(
        {item["theme"] for item in _load_wordlists(language=language)}
    )
    return [(theme, THEME_LABELS.get(theme, theme.capitalize())) for theme in themes]


@router.message(F.text == "🔤 Слова")
async def start_vocabulary(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    profile = await ctx.users.get_profile(
        message.from_user.id,
        message.from_user.username,
    )
    if not profile.onboarding_completed:
        await message.answer("Сначала выбери язык и пройди настройку: /start")
        return
    session = ctx.user_sessions.setdefault(message.from_user.id, {})
    if session.get("daily"):
        session["daily"]["active"] = False
    await state.clear()
    await send_vocabulary_menu(message, message.from_user.id)


@router.callback_query(F.data == "vocab:menu")
async def vocabulary_menu(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    session = ctx.user_sessions.setdefault(callback.from_user.id, {})
    if session.get("daily"):
        session["daily"]["active"] = False
    await state.clear()
    await callback.answer()
    await send_vocabulary_menu(callback.message, callback.from_user.id)


async def send_vocabulary_menu(message: Message, user_id: int) -> None:
    ctx = get_app_context()
    due_count = await ctx.vocabulary.get_due_count(user_id)
    learned_today = await ctx.vocabulary.get_words_learned_today(user_id)
    stats = await ctx.db.get_stats(user_id)
    text = (
        "🔤 Слова\n\n"
        f"Сегодня добавлено: {learned_today}/{ctx.settings.max_new_words_per_day}\n"
        f"Нужно повторить: {due_count}\n"
        f"В изучении: {stats['words_learning']}\n"
        f"Освоено: {stats['words_mastered']}\n\n"
        "Рекомендуемая порция — 5 слов. Если есть силы, можно взять ещё."
    )
    await message.answer(
        text,
        reply_markup=vocabulary_menu_keyboard(
            due_count,
            learned_today,
            ctx.settings.max_new_words_per_day,
        ),
    )


@router.callback_query(F.data == "vocab:themes")
async def choose_vocabulary_theme(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    ctx = get_app_context()
    language = await ctx.db.get_learning_language(callback.from_user.id)
    _cancel_daily(callback.from_user.id)
    await state.clear()
    await callback.answer()
    await callback.message.answer(
        "Выбери тему для следующей порции:",
        reply_markup=vocabulary_theme_keyboard(_available_themes(language)),
    )


@router.callback_query(F.data == "vocab:stats")
async def vocabulary_stats(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    _cancel_daily(callback.from_user.id)
    await state.clear()
    stats = await ctx.db.get_stats(callback.from_user.id)
    await callback.answer()
    await callback.message.answer(
        "📊 Словарный прогресс\n\n"
        f"Встречено: {stats['words_introduced']}\n"
        f"В изучении: {stats['words_learning']}\n"
        f"Освоено: {stats['words_mastered']}\n"
        f"Повторить сегодня: {stats['words_due']}"
    )
    await send_vocabulary_menu(callback.message, callback.from_user.id)


@router.callback_query(F.data == "vocab:start_review")
async def start_review(callback: CallbackQuery, state: FSMContext) -> None:
    _cancel_daily(callback.from_user.id)
    await callback.answer()
    started = await start_review_session(
        callback.message,
        state,
        callback.from_user.id,
    )
    if not started:
        await callback.message.answer("На сегодня повторений нет.")
        await send_vocabulary_menu(callback.message, callback.from_user.id)


async def start_review_session(
    message: Message,
    state: FSMContext,
    user_id: int,
) -> bool:
    ctx = get_app_context()
    due = await ctx.vocabulary.get_due_reviews(
        user_id,
        limit=ctx.settings.review_words_per_session,
    )
    if not due:
        return False
    language = await ctx.db.get_learning_language(user_id)
    session = ctx.user_sessions.setdefault(user_id, {})
    session.update(
        {
            "vocab_reviews": due,
            "review_index": 0,
            "vocab_language": language,
        }
    )
    await state.set_state(VocabularyStates.reviewing)
    await message.answer(f"🔁 Активное повторение: {len(due)} слов")
    await _send_review_front(message, user_id)
    return True


@router.callback_query(F.data.startswith("vocab:new:"))
async def new_vocabulary_batch(callback: CallbackQuery, state: FSMContext) -> None:
    theme = callback.data.split(":", 2)[-1]
    theme_filter = None if theme == "auto" else theme
    _cancel_daily(callback.from_user.id)
    await state.clear()
    await callback.answer()
    await learn_new_batch(
        callback.message,
        state,
        callback.from_user.id,
        theme_filter=theme_filter,
    )


async def learn_new_batch(
    message: Message,
    state: FSMContext,
    user_id: int,
    theme_filter: str | None = None,
    batch_limit: int | None = None,
) -> int:
    ctx = get_app_context()
    profile = await ctx.users.get_profile(user_id)
    learned_today = await ctx.vocabulary.get_words_learned_today(user_id)
    remaining = max(0, ctx.settings.max_new_words_per_day - learned_today)
    requested = batch_limit or ctx.settings.new_words_per_day
    batch_size = min(requested, remaining)
    if batch_size == 0:
        await message.answer(
            f"Сегодня уже добавлено {learned_today} новых слов — это дневной максимум. "
            "Лучше закрепить их повторением."
        )
        if not await _continue_daily(message, state, user_id, "vocabulary"):
            await send_vocabulary_menu(message, user_id)
        return 0

    all_words = _load_wordlists(theme_filter, profile.learning_language)
    random.shuffle(all_words)
    new_words = []
    for item in all_words:
        if await ctx.vocabulary.user_has_word(
            user_id,
            item["word"],
            profile.learning_language,
        ):
            continue
        new_words.append(item)
        if len(new_words) >= batch_size:
            break

    if not new_words:
        theme_name = THEME_LABELS.get(theme_filter or "", "выбранной теме")
        await message.answer(
            f"В теме «{theme_name}» новых слов больше нет. Выбери другую тему."
        )
        if not await _continue_daily(message, state, user_id, "vocabulary"):
            await send_vocabulary_menu(message, user_id)
        return 0

    theme_text = (
        f" · {THEME_LABELS.get(theme_filter, theme_filter)}"
        if theme_filter
        else ""
    )
    await message.answer(f"🔤 Новая порция: {len(new_words)} слов{theme_text}")
    for item in new_words:
        is_english = profile.learning_language == "english"
        dict_data = (
            await ctx.dictionary.lookup(item["word"])
            if is_english
            else {}
        )
        examples = (
            await ctx.tatoeba.get_examples(item["word"], limit=1)
            if is_english
            else []
        )
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
            language=profile.learning_language,
        )
        text = (
            f"📝 <b>{html.escape(item['word'])}</b> "
            f"[{html.escape(str(dict_data.get('phonetic') or ''))}]\n"
            f"Перевод: {html.escape(item['translation'])}\n"
        )
        if example_en:
            text += f"Пример: {html.escape(str(example_en))}"
            if example_ru:
                text += f" ({html.escape(str(example_ru))})"
        await message.answer(text, parse_mode="HTML")
        if is_english:
            audio_path = await ctx.tts.get_word_audio(
                item["word"],
                dict_data.get("audio_url", ""),
            )
        else:
            audio_path = await ctx.tts.synthesize(
                item["word"],
                lang=str(language_info(profile.learning_language)["tts"]),
            )
        if audio_path:
            await message.answer_voice(FSInputFile(audio_path))

    count = await ctx.vocabulary.get_words_count(
        user_id,
        profile.learning_language,
    )
    if count >= 10:
        await ctx.db.unlock_achievement(user_id, "ten_words")
    await ctx.progress.record_lesson(
        user_id,
        "vocabulary",
        "new_words",
        score=100,
        language=profile.learning_language,
    )
    await ctx.db.touch_activity(user_id)
    await message.answer(
        f"Порция завершена. Эти слова пока в статусе «изучаются».\n"
        f"Всего встречено слов: {count}"
    )
    if not await _continue_daily(message, state, user_id, "vocabulary"):
        await send_vocabulary_menu(message, user_id)
    return len(new_words)


@router.callback_query(
    VocabularyStates.reviewing,
    F.data.startswith("vocab:reveal:"),
)
async def reveal_review_answer(callback: CallbackQuery) -> None:
    ctx = get_app_context()
    user_id = callback.from_user.id
    card = _current_review_card(user_id)
    if not card:
        await callback.answer("Сессия устарела", show_alert=True)
        return
    word_id = int(callback.data.split(":")[-1])
    if int(card["id"]) != word_id:
        await callback.answer("Эта карточка уже закрыта", show_alert=True)
        return
    details = (
        f"<b>{html.escape(card['word'])}</b> — "
        f"{html.escape(card['translation'])}"
    )
    if card.get("example_en"):
        details += f"\n\n{html.escape(str(card['example_en']))}"
        if card.get("example_ru"):
            details += f" ({html.escape(str(card['example_ru']))})"
    await callback.message.edit_text(
        details + "\n\nНасколько легко ты вспомнил(а) перевод?",
        parse_mode="HTML",
        reply_markup=review_quality_keyboard(word_id),
    )
    await callback.answer()


@router.callback_query(VocabularyStates.reviewing, F.data.startswith("vocab:review:"))
async def review_word(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    user_id = callback.from_user.id
    _, _, word_id, quality = callback.data.split(":")
    session = ctx.user_sessions.get(user_id, {})
    reviews = session.get("vocab_reviews", [])
    current = _current_review_card(user_id)
    if not reviews or not current or int(current["id"]) != int(word_id):
        await callback.answer("Сессия устарела", show_alert=True)
        await state.clear()
        return
    await ctx.vocabulary.review_word(
        user_id,
        int(word_id),
        int(quality),
        language=session.get("vocab_language", "english"),
    )
    idx = int(session.get("review_index", 0)) + 1
    session["review_index"] = idx
    ctx.user_sessions[user_id] = session
    await callback.message.edit_text(
        f"{callback.message.text}\n\nЗаписано ✅",
        parse_mode=None,
    )
    await callback.answer()
    if idx >= len(reviews):
        await state.clear()
        await ctx.progress.record_lesson(
            user_id,
            "vocabulary",
            "review",
            score=100,
            language=session.get("vocab_language", "english"),
        )
        await callback.message.answer("🔁 Повторение завершено!")
        if not await _continue_daily(
            callback.message,
            state,
            user_id,
            "review",
        ):
            await send_vocabulary_menu(callback.message, user_id)
        return
    await _send_review_front(callback.message, user_id)


def _current_review_card(user_id: int) -> dict | None:
    ctx = get_app_context()
    session = ctx.user_sessions.get(user_id, {})
    reviews = session.get("vocab_reviews", [])
    idx = int(session.get("review_index", 0))
    if idx >= len(reviews):
        return None
    return reviews[idx]


async def _send_review_front(message: Message, user_id: int) -> None:
    ctx = get_app_context()
    session = ctx.user_sessions.get(user_id, {})
    reviews = session.get("vocab_reviews", [])
    idx = int(session.get("review_index", 0))
    card = _current_review_card(user_id)
    if not card:
        return
    text = (
        f"Карточка {idx + 1}/{len(reviews)}\n"
        f"Как переводится слово <b>{html.escape(card['word'])}</b>?\n\n"
        "Сначала попробуй вспомнить без подсказки."
    )
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=review_reveal_keyboard(card["id"]),
    )


async def _continue_daily(
    message: Message,
    state: FSMContext,
    user_id: int,
    completed_step: str,
) -> bool:
    ctx = get_app_context()
    daily = ctx.user_sessions.get(user_id, {}).get("daily", {})
    if not daily.get("active"):
        return False
    from bot.handlers.daily import continue_daily

    await continue_daily(message, state, user_id, completed_step)
    return True


def _cancel_daily(user_id: int) -> None:
    ctx = get_app_context()
    daily = ctx.user_sessions.setdefault(user_id, {}).get("daily")
    if daily:
        daily["active"] = False
