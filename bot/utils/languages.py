from typing import Any


DEFAULT_LANGUAGE = "english"

LEARNING_LANGUAGES: dict[str, dict[str, str]] = {
    "english": {
        "label": "🇬🇧 Английский",
        "name_ru": "английский",
        "name_en": "English",
        "tts": "en",
    },
    "italian": {
        "label": "🇮🇹 Итальянский",
        "name_ru": "итальянский",
        "name_en": "Italian",
        "tts": "it",
    },
}

ITALIAN_LEVEL_QUESTIONS = [
    {
        "question": "Что значит итальянское слово «ciao»?",
        "options": ["Привет", "Спасибо", "Извините"],
        "correct_index": 0,
    },
    {
        "question": "Выбери перевод: «Io sono Marco».",
        "options": ["Я вижу Марко", "Я — Марко", "Я знаю Марко"],
        "correct_index": 1,
    },
    {
        "question": "Какой артикль подходит: ___ casa?",
        "options": ["la", "il", "lo"],
        "correct_index": 0,
    },
    {
        "question": "Выбери правильную фразу: «Мы друзья».",
        "options": ["Noi sono amici", "Noi siamo amici", "Noi siete amici"],
        "correct_index": 1,
    },
    {
        "question": "Что значит «grazie»?",
        "options": ["До свидания", "Пожалуйста", "Спасибо"],
        "correct_index": 2,
    },
]


def language_info(code: str | None) -> dict[str, Any]:
    return LEARNING_LANGUAGES.get(code or "", LEARNING_LANGUAGES[DEFAULT_LANGUAGE])


def language_label(code: str | None) -> str:
    return str(language_info(code)["label"])
