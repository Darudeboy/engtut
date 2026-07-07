ACHIEVEMENTS = {
    "first_lesson": "🎉 Первый урок",
    "ten_words": "🔤 10 слов",
    "seven_day_streak": "🔥 7 дней подряд",
    "first_dialogue": "💬 Первый диалог",
    "writing_level_3": "✍️ Уровень письма 3",
}

GRAMMAR_TOPICS = [
    "to be",
    "pronouns",
    "articles",
    "present simple",
    "questions",
    "past simple",
    "future simple",
]

LEVEL_QUESTIONS = [
    {
        "question": "Что значит слово 'hello'?",
        "options": ["Пока", "Привет", "Спасибо"],
        "correct_index": 1,
    },
    {
        "question": "Выберите перевод: 'I am a student'",
        "options": ["Я учитель", "Я студент", "Я врач"],
        "correct_index": 1,
    },
    {
        "question": "Какой артикль перед 'apple'?",
        "options": ["a", "an", "the"],
        "correct_index": 1,
    },
    {
        "question": "Где правильный порядок слов?",
        "options": ["student I am", "I am student", "I am a student"],
        "correct_index": 2,
    },
    {
        "question": "Что значит 'book'?",
        "options": ["Книга", "Дом", "Вода"],
        "correct_index": 0,
    },
]

WRITING_LEVELS = {
    1: {
        "title": "Дополнение одним словом",
        "prompt": "Tom ___ in London. (живёт)\nНапишите одно слово:",
        "answer": "lives",
    },
    2: {
        "title": "Перевод слова",
        "prompt": "Как будет «кофе» по-английски? Напишите одно слово:",
        "answer": "coffee",
    },
    3: {
        "title": "Перевод фразы",
        "prompt": "Переведите: «Я студент»\nНапишите ответ:",
        "answer": "I am a student",
    },
    4: {
        "title": "Составление предложения",
        "prompt": "Составьте предложение из слов: student / I / am / a",
        "answer": "I am a student",
    },
    5: {
        "title": "Свободный ответ",
        "prompt": "What is your name? (Как тебя зовут?)\nНапишите ответ на английском (2–3 слова):",
        "answer": "My name is",
        "free": True,
    },
}

LISTENING_RESOURCES = [
    {
        "title": "VOA Learning English",
        "url": "https://learningenglish.voanews.com/",
        "description": "Новости и уроки на упрощённом английском.",
    },
    {
        "title": "BBC Learning English - 6 Minute English",
        "url": "https://www.bbc.co.uk/learningenglish/english/features/6-minute-english",
        "description": "Короткие подкасты для начинающих.",
    },
]
