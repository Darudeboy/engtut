"""Учебные материалы по итальянскому языку для русскоязычных начинающих."""

ITALIAN_GRAMMAR_TOPICS_BY_LEVEL = {
    "Pre-A1": [
        "Личные местоимения: io, tu, lui, lei, noi, voi, loro",
        "Глагол essere в настоящем времени",
        "Глагол avere в настоящем времени",
        "Определённые артикли: il, lo, la, i, gli, le",
        "Неопределённые артикли: un, uno, una, un’",
        "Род и число существительных",
        "Базовый порядок слов и простое отрицание с non",
        "Вопросительные слова: chi, che cosa, dove, come",
    ],
    "A1": [
        "Настоящее время правильных глаголов на -are, -ere, -ire",
        "Частотные неправильные глаголы: andare, fare, stare, venire",
        "Согласование прилагательных с существительными",
        "Притяжательные прилагательные и артикль",
        "Предлоги места и времени: a, in, da, di, con, per",
        "Слитные формы предлогов с артиклями",
        "Модальные глаголы potere, dovere и volere",
        "Возвратные глаголы и распорядок дня",
        "Конструкция c’è / ci sono",
        "Прошедшее время passato prossimo с avere и essere",
    ],
    "A2": [
        "Passato prossimo: выбор вспомогательного глагола и согласование",
        "Imperfetto: описание фона, привычек и состояний в прошлом",
        "Passato prossimo и imperfetto в одном рассказе",
        "Прямые местоимения lo, la, li, le и косвенные mi, ti, gli, le",
        "Частица ci для места и частица ne для количества",
        "Сравнительная и превосходная степени прилагательных",
        "Будущее время futuro semplice",
        "Повелительное наклонение в неформальном общении",
        "Условные предложения реального типа с se",
        "Связки perché, quindi, però, mentre и invece",
    ],
}


ITALIAN_WRITING_STAGES = {
    1: [
        {
            "id": "it_gap_sono",
            "title": "Вставь одно слово",
            "prompt": "Io ___ di Mosca. (я из Москвы)",
            "answer": "sono",
        },
        {
            "id": "it_gap_ha",
            "title": "Вставь одно слово",
            "prompt": "Marco ___ un cane. (у Марко есть собака)",
            "answer": "ha",
        },
        {
            "id": "it_gap_abiti",
            "title": "Вставь одно слово",
            "prompt": "Dove ___? (Где ты живёшь?)",
            "answer": "abiti",
        },
    ],
    2: [
        {
            "id": "it_word_water",
            "title": "Перевод слова",
            "prompt": "Как будет «вода» по-итальянски?",
            "answer": "acqua",
        },
        {
            "id": "it_word_family",
            "title": "Перевод слова",
            "prompt": "Как будет «семья» по-итальянски?",
            "answer": "famiglia",
        },
        {
            "id": "it_word_today",
            "title": "Перевод слова",
            "prompt": "Как будет «сегодня» по-итальянски?",
            "answer": "oggi",
        },
    ],
    3: [
        {
            "id": "it_phrase_student",
            "title": "Перевод фразы",
            "prompt": "Переведи на итальянский: «Я студент».",
            "answer": "Sono uno studente",
        },
        {
            "id": "it_phrase_coffee",
            "title": "Перевод фразы",
            "prompt": "Переведи на итальянский: «Я люблю кофе».",
            "answer": "Mi piace il caffè",
        },
        {
            "id": "it_phrase_rome",
            "title": "Перевод фразы",
            "prompt": "Переведи на итальянский: «Мы живём в Риме».",
            "answer": "Abitiamo a Roma",
        },
    ],
    4: [
        {
            "id": "it_order_name",
            "title": "Собери предложение",
            "prompt": "chiamo / Mi / Anna",
            "answer": "Mi chiamo Anna",
        },
        {
            "id": "it_order_breakfast",
            "title": "Собери предложение",
            "prompt": "colazione / mattina / Faccio / ogni",
            "answer": "Faccio colazione ogni mattina",
        },
        {
            "id": "it_order_question",
            "title": "Собери вопрос",
            "prompt": "il / costa / biglietto / Quanto",
            "answer": "Quanto costa il biglietto",
        },
    ],
    5: [
        {
            "id": "it_personal_home",
            "title": "Личный ответ",
            "prompt": "Расскажи по-итальянски, где ты живёшь. Напиши 1–2 предложения.",
            "reference": "Abito in una piccola città. La mia casa è vicino al centro.",
            "requirements": "Указать место проживания; написать 1–2 понятных предложения.",
            "min_words": 5,
            "free": True,
        },
        {
            "id": "it_personal_hobby",
            "title": "Личный ответ",
            "prompt": "Расскажи по-итальянски о любимом занятии. Напиши 1–2 предложения.",
            "reference": "Nel tempo libero mi piace leggere e ascoltare la musica.",
            "requirements": "Назвать хотя бы одно занятие; написать 1–2 предложения.",
            "min_words": 6,
            "free": True,
        },
        {
            "id": "it_personal_family",
            "title": "Личный ответ",
            "prompt": "Кратко расскажи по-итальянски о своей семье. Напиши 1–2 предложения.",
            "reference": "Ho una famiglia piccola. Vivo con mia moglie e mio figlio.",
            "requirements": "Сообщить хотя бы один факт о семье; написать 1–2 предложения.",
            "min_words": 7,
            "free": True,
        },
    ],
    6: [
        {
            "id": "it_daily_routine",
            "title": "Связный ответ",
            "prompt": "Опиши по-итальянски своё обычное утро. Напиши 2–3 предложения.",
            "reference": "Mi sveglio alle sette. Faccio colazione e poi vado al lavoro.",
            "requirements": "Описать не менее двух утренних действий; написать 2–3 предложения.",
            "min_words": 10,
            "free": True,
        },
        {
            "id": "it_last_weekend",
            "title": "Связный ответ",
            "prompt": "Расскажи по-итальянски, что ты делал в прошлые выходные. Напиши 2–3 предложения.",
            "reference": "Sabato ho visitato i miei amici. Abbiamo cenato insieme e abbiamo visto un film.",
            "requirements": "Использовать passato prossimo и назвать не менее двух действий.",
            "min_words": 12,
            "free": True,
        },
        {
            "id": "it_future_plans",
            "title": "Связный ответ",
            "prompt": "Расскажи по-итальянски о планах на следующие выходные. Напиши 2–3 предложения.",
            "reference": "Sabato andrò al mercato. Domenica resterò a casa e leggerò un libro.",
            "requirements": "Описать не менее двух будущих действий; написать 2–3 предложения.",
            "min_words": 11,
            "free": True,
        },
    ],
    7: [
        {
            "id": "it_message_late",
            "title": "Практическое сообщение",
            "prompt": "Напиши другу по-итальянски, что опоздаешь на 20 минут, и извинись. 3–4 предложения.",
            "reference": "Ciao! Mi dispiace, ma arriverò con venti minuti di ritardo. Aspettami, per favore.",
            "requirements": "Поздороваться, извиниться и указать время опоздания.",
            "min_words": 14,
            "free": True,
        },
        {
            "id": "it_hotel_request",
            "title": "Практическое сообщение",
            "prompt": "Напиши в отель по-итальянски: попроси тихий номер и уточни время заселения. 3–4 предложения.",
            "reference": "Buongiorno. Vorrei una camera tranquilla, per favore. A che ora posso fare il check-in?",
            "requirements": "Вежливо попросить тихий номер и задать вопрос о заселении.",
            "min_words": 14,
            "free": True,
        },
        {
            "id": "it_invite_friend",
            "title": "Практическое сообщение",
            "prompt": "Пригласи друга по-итальянски в кафе в субботу и предложи время. 3–4 предложения.",
            "reference": "Ciao! Vuoi andare al bar sabato? Possiamo incontrarci alle sei davanti alla stazione.",
            "requirements": "Пригласить, назвать день и предложить время и место встречи.",
            "min_words": 14,
            "free": True,
        },
    ],
    8: [
        {
            "id": "it_opinion_city",
            "title": "Мнение с аргументом",
            "prompt": "Хорошо ли жить в твоём городе? Ответь по-итальянски в 4–6 предложениях и используй perché.",
            "reference": "Mi piace vivere nella mia città perché è tranquilla e verde. Ci sono molti parchi e i trasporti sono comodi. Però in inverno fa molto freddo.",
            "requirements": "Высказать мнение, привести причину с perché; написать 4–6 предложений.",
            "min_words": 25,
            "free": True,
        },
        {
            "id": "it_story_trip",
            "title": "Короткая история",
            "prompt": "Расскажи по-итальянски о запомнившейся поездке. Напиши 4–6 предложений.",
            "reference": "L'estate scorsa sono andato al mare con la mia famiglia. Siamo rimasti lì per una settimana. Ogni giorno nuotavamo e la sera passeggiavamo. È stato un viaggio bellissimo.",
            "requirements": "Указать когда, куда и с кем ездил; описать события в прошлом.",
            "min_words": 28,
            "free": True,
        },
        {
            "id": "it_compare_transport",
            "title": "Сравнение",
            "prompt": "Что лучше: автомобиль или общественный транспорт? Ответь по-итальянски в 4–6 предложениях.",
            "reference": "Secondo me, i mezzi pubblici sono più economici dell'auto. L'auto è più comoda, ma costa molto. In città preferisco prendere la metropolitana perché è veloce.",
            "requirements": "Сравнить два варианта и объяснить свой выбор.",
            "min_words": 25,
            "free": True,
        },
    ],
}


ITALIAN_EXAMS = {
    "A1": {
        "source_level": "Pre-A1",
        "questions": [
            {
                "section": "vocabulary",
                "prompt": "Выбери перевод слова «дом».",
                "options": ["casa", "scuola", "strada"],
                "correct_index": 0,
            },
            {
                "section": "vocabulary",
                "prompt": "Что означает итальянское слово «pane»?",
                "options": ["молоко", "хлеб", "рис"],
                "correct_index": 1,
            },
            {
                "section": "vocabulary",
                "prompt": "Как по-итальянски сказать «спасибо»?",
                "options": ["scusa", "grazie", "prego"],
                "correct_index": 1,
            },
            {
                "section": "vocabulary",
                "prompt": "Выбери итальянское название дня «понедельник».",
                "options": ["sabato", "domenica", "lunedì"],
                "correct_index": 2,
            },
            {
                "section": "vocabulary",
                "prompt": "Какое слово обозначает «сестру»?",
                "options": ["sorella", "fratello", "madre"],
                "correct_index": 0,
            },
            {
                "section": "grammar",
                "prompt": "Выбери правильную форму: Io ___ russo.",
                "options": ["sei", "sono", "è"],
                "correct_index": 1,
            },
            {
                "section": "grammar",
                "prompt": "Выбери правильный артикль: ___ amico.",
                "options": ["un", "una", "uno"],
                "correct_index": 0,
            },
            {
                "section": "grammar",
                "prompt": "Закончи предложение: Maria ___ a Roma.",
                "options": ["abito", "abiti", "abita"],
                "correct_index": 2,
            },
            {
                "section": "grammar",
                "prompt": "Выбери правильное отрицание: Non ___ il caffè.",
                "options": ["bevo", "bevi", "beve"],
                "correct_index": 0,
            },
            {
                "section": "grammar",
                "prompt": "Как правильно спросить «Где ты живёшь?»",
                "options": ["Dove abiti?", "Come abiti?", "Quando abiti?"],
                "correct_index": 0,
            },
            {
                "section": "reading",
                "passage": (
                    "Ciao! Mi chiamo Giulia e ho diciannove anni. Abito a Bologna "
                    "con i miei genitori e mio fratello Luca. Studio italiano "
                    "all'università. La mattina bevo tè e mangio pane con marmellata. "
                    "Nel pomeriggio lavoro in una piccola libreria."
                ),
                "prompt": "Как зовут девушку?",
                "options": ["Giulia", "Lucia", "Anna"],
                "correct_index": 0,
            },
            {
                "section": "reading",
                "prompt": "Сколько ей лет?",
                "options": ["diciassette anni", "diciannove anni", "vent'anni"],
                "correct_index": 1,
            },
            {
                "section": "reading",
                "prompt": "В каком городе она живёт?",
                "options": ["a Roma", "a Milano", "a Bologna"],
                "correct_index": 2,
            },
            {
                "section": "reading",
                "prompt": "Что Джулия пьёт утром?",
                "options": ["tè", "caffè", "latte"],
                "correct_index": 0,
            },
            {
                "section": "reading",
                "prompt": "Где она работает после обеда?",
                "options": ["in un bar", "in una libreria", "in una scuola"],
                "correct_index": 1,
            },
        ],
    },
    "A2": {
        "source_level": "A1",
        "questions": [
            {
                "section": "vocabulary",
                "prompt": "Выбери итальянское выражение со значением «опоздать».",
                "options": ["essere in ritardo", "avere fretta", "fare una pausa"],
                "correct_index": 0,
            },
            {
                "section": "vocabulary",
                "prompt": "Как по-итальянски называется «расписание»?",
                "options": ["il binario", "l'orario", "il viaggio"],
                "correct_index": 1,
            },
            {
                "section": "vocabulary",
                "prompt": "Выбери выражение со значением «записаться на приём».",
                "options": ["prendere un appuntamento", "perdere il treno", "fare la spesa"],
                "correct_index": 0,
            },
            {
                "section": "vocabulary",
                "prompt": "Какое слово означает «дешёвый»?",
                "options": ["caro", "comodo", "economico"],
                "correct_index": 2,
            },
            {
                "section": "vocabulary",
                "prompt": "Выбери итальянский глагол со значением «одалживать, брать взаймы».",
                "options": ["restituire", "prendere in prestito", "regalare"],
                "correct_index": 1,
            },
            {
                "section": "grammar",
                "prompt": "Выбери правильную форму passato prossimo: Ieri noi ___ al cinema.",
                "options": ["siamo andati", "abbiamo andato", "andavamo"],
                "correct_index": 0,
            },
            {
                "section": "grammar",
                "prompt": "Выбери правильную форму: Da piccolo, Marco ___ al mare ogni estate.",
                "options": ["è andato", "andava", "andrà"],
                "correct_index": 1,
            },
            {
                "section": "grammar",
                "prompt": "Замени выделяемое дополнение местоимением: Compro la torta → ___ compro.",
                "options": ["Le", "La", "Gli"],
                "correct_index": 1,
            },
            {
                "section": "grammar",
                "prompt": "Выбери сравнительную форму: Il treno è ___ dell'autobus.",
                "options": ["più veloce", "velocissimo", "il più veloce"],
                "correct_index": 0,
            },
            {
                "section": "grammar",
                "prompt": "Закончи реальное условие: Se domani piove, ___ a casa.",
                "options": ["restavo", "sono restato", "resterò"],
                "correct_index": 2,
            },
            {
                "section": "reading",
                "passage": (
                    "Sabato scorso Elena voleva visitare Firenze con la sua amica "
                    "Paola. Sono partite presto, ma il loro treno ha avuto quaranta "
                    "minuti di ritardo. Quando sono arrivate, pioveva forte. Hanno "
                    "visitato un museo e poi hanno pranzato in una trattoria vicino "
                    "al centro. Nel pomeriggio è uscito il sole, quindi hanno "
                    "passeggiato lungo il fiume. Elena era stanca, ma molto contenta."
                ),
                "prompt": "Куда хотели поехать Елена и Паола?",
                "options": ["a Firenze", "a Venezia", "a Bologna"],
                "correct_index": 0,
            },
            {
                "section": "reading",
                "prompt": "Почему они приехали позже запланированного?",
                "options": [
                    "Hanno perso il treno.",
                    "Il treno era in ritardo.",
                    "Sono uscite tardi di casa.",
                ],
                "correct_index": 1,
            },
            {
                "section": "reading",
                "prompt": "Какая погода была, когда они приехали?",
                "options": ["Pioveva forte.", "Nevicava.", "C'era il sole."],
                "correct_index": 0,
            },
            {
                "section": "reading",
                "prompt": "Где они пообедали?",
                "options": ["In un albergo.", "In un bar alla stazione.", "In una trattoria."],
                "correct_index": 2,
            },
            {
                "section": "reading",
                "prompt": "Что они делали после того, как вышло солнце?",
                "options": [
                    "Hanno visitato un altro museo.",
                    "Hanno passeggiato lungo il fiume.",
                    "Sono tornate subito a casa.",
                ],
                "correct_index": 1,
            },
        ],
    },
}
