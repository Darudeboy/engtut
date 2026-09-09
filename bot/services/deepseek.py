import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any

import openai

from bot.config import PROMPTS_DIR, Settings
from bot.utils.languages import language_info

logger = logging.getLogger(__name__)


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise


class DeepSeekService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = None
        if settings.deepseek_api_key:
            self.client = openai.OpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
            )

    @property
    def available(self) -> bool:
        return self.client is not None

    def _chat(self, system: str, user: str, temperature: float = 0.4) -> str:
        if not self.client:
            raise RuntimeError("DeepSeek API key is not configured")
        response = self.client.chat.completions.create(
            model=self.settings.deepseek_model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""

    async def generate_reading_lesson(
        self,
        topic: str,
        level: str = "Pre-A1",
        variant: int = 0,
        focus_words: list[str] | None = None,
        language: str = "english",
    ) -> dict[str, Any]:
        target = language_info(language)["name_en"]
        system = (
            f"You are a friendly {target} tutor for Russian-speaking learners. "
            "Explanations and translations must be in Russian."
        )
        word_range = {
            "Pre-A1": "45-70",
            "A1": "80-120",
            "A2": "130-180",
        }.get(level, "80-120")
        user = (
            f"Create variation {variant} of a {level} reading lesson about '{topic}'. "
            f"The {target}-only text must contain {word_range} words.\n"
            "Return JSON only with keys: title, text, keywords (4-6 items with "
            "word and Russian translation), questions. Create exactly 4 questions: "
            "main idea, factual detail, vocabulary in context, and sequence or "
            "inference. Each has question, exactly 3 options, correct_index, "
            "explanation_ru. Distractors must be plausible."
        )
        if focus_words:
            user += (
                "\nNaturally include these learner vocabulary words when possible: "
                + ", ".join(focus_words)
                + "."
            )
        try:
            content = self._chat(system, user, temperature=0.3)
            result = _extract_json(content)
            questions = result.get("questions", [])
            if (
                not result.get("text")
                or len(questions) != 4
                or any(len(item.get("options", [])) != 3 for item in questions)
            ):
                raise ValueError("Invalid reading lesson")
            return result
        except Exception as exc:
            logger.warning("DeepSeek reading fallback: %s", exc)
            return self._fallback_reading(topic, level, language)

    async def generate_grammar_exercise(
        self,
        topic: str,
        level: str = "Pre-A1",
        variant: int = 0,
        language: str = "english",
    ) -> dict[str, Any]:
        target = language_info(language)["name_en"]
        system = (
            f"You are a {target} grammar tutor for Russian-speaking learners. "
            "Explain grammar in Russian."
        )
        user = (
            f"Create variation {variant} of a grammar lesson on '{topic}' "
            f"for level {level}.\n"
            "Return JSON only: explanation_ru, questions. Create exactly 5 "
            "questions with a mix of gap choice, sentence choice, correction, "
            "and meaning in context. Each question has prompt, exactly 3 options, "
            "correct_index, hint_ru. Do not repeat the same sentence pattern."
        )
        try:
            content = self._chat(system, user, temperature=0.3)
            result = _extract_json(content)
            questions = result.get("questions", [])
            if (
                len(questions) != 5
                or any(len(item.get("options", [])) != 3 for item in questions)
            ):
                raise ValueError("Invalid grammar lesson")
            return result
        except Exception as exc:
            logger.warning("DeepSeek grammar fallback: %s", exc)
            return self._fallback_grammar(topic, language)

    async def generate_listening_lesson(
        self,
        topic: str,
        level: str,
        variant: int,
        language: str = "english",
    ) -> dict[str, Any]:
        target = language_info(language)["name_en"]
        system = (
            f"Create a short level-appropriate {target} listening task "
            "for a Russian-speaking learner."
        )
        user = (
            f"CEFR level: {level}. Topic: {topic}. Variation: {variant}.\n"
            "Return JSON only with: title, transcript, questions. "
            "Create exactly 3 questions. Each question must contain question, "
            "exactly 3 options, correct_index, explanation_ru. "
            "Test gist and concrete details from the transcript. "
            f"The transcript must contain only {target}, with no Russian words."
        )
        try:
            content = self._chat(system, user, temperature=0.4)
            result = _extract_json(content)
            questions = result.get("questions", [])
            if (
                not result.get("transcript")
                or len(questions) != 3
                or any(len(item.get("options", [])) != 3 for item in questions)
            ):
                raise ValueError("Invalid listening lesson")
            return result
        except Exception as exc:
            logger.warning("DeepSeek listening fallback: %s", exc)
            return self._fallback_listening(level, topic, language)

    async def check_writing_answer(
        self,
        target_phrase: str,
        user_answer: str,
        level: str = "Pre-A1",
        language: str = "english",
    ) -> dict[str, Any]:
        target = language_info(language)["name_en"]
        system = f"Evaluate beginner {target} answers gently. Reply in Russian."
        user = (
            f'Learner level: {level}. Expected: "{target_phrase}". '
            f'Answer: "{user_answer}". '
            'Return JSON: {"status":"correct|close|incorrect","feedback":"...","correct_answer":"..."}'
        )
        try:
            content = self._chat(system, user, temperature=0.2)
            return _extract_json(content)
        except Exception as exc:
            logger.warning("DeepSeek writing check fallback: %s", exc)
            return self._fallback_writing_check(target_phrase, user_answer)

    async def check_writing_task(
        self,
        prompt: str,
        requirements: str,
        reference: str,
        user_answer: str,
        level: str,
        min_words: int,
        language: str = "english",
    ) -> dict[str, Any]:
        target = language_info(language)["name_en"]
        system = (
            f"You assess short {target} writing by beginner learners. "
            "Judge whether the answer communicates the requested meaning. "
            "Do not require an exact match with the example. Be supportive, "
            "but mark an answer correct only when it follows the requirements."
        )
        user = (
            f"CEFR level: {level}\n"
            f"Task: {prompt}\n"
            f"Requirements: {requirements}\n"
            f"Reference example (not the only valid answer): {reference}\n"
            f"Minimum words: {min_words}\n"
            f"Learner answer: {user_answer}\n\n"
            "Return JSON only: "
            '{"status":"correct|close|incorrect",'
            '"feedback":"brief feedback in Russian",'
            '"correct_answer":"a natural corrected version of the learner answer"}'
        )
        try:
            content = self._chat(system, user, temperature=0.2)
            result = _extract_json(content)
            if result.get("status") not in {"correct", "close", "incorrect"}:
                raise ValueError("Invalid writing assessment status")
            return result
        except Exception as exc:
            logger.warning("DeepSeek open writing check fallback: %s", exc)
            words = re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)?", user_answer, re.UNICODE)
            if len(words) < min_words:
                return {
                    "status": "incorrect",
                    "feedback": (
                        f"Нужно написать не менее {min_words} слов. "
                        f"Сейчас: {len(words)}."
                    ),
                    "correct_answer": reference,
                }
            return {
                "status": "correct",
                "feedback": "Требуемый объём выполнен. Продолжай развивать ответ!",
                "correct_answer": user_answer,
            }

    async def dialogue_reply(
        self,
        scenario: str,
        role: str,
        history: list[dict[str, str]],
        level: str = "Pre-A1",
        success_criteria: list[str] | None = None,
        language: str = "english",
    ) -> str:
        target = language_info(language)["name_en"]
        system = (
            f"You are {role} in this situation: {scenario}. "
            f"Speak only {target}, at CEFR level {level}. "
            "If the learner writes in Russian, include a short Russian translation."
        )
        if success_criteria:
            system += (
                "\nHelp the learner naturally achieve these goals: "
                + "; ".join(success_criteria)
                + ". Do not list the goals to the learner."
            )
        messages = [{"role": "system", "content": system}]
        messages.extend(history)
        if not self.client:
            return self._fallback_dialogue_reply(scenario, history, language)
        try:
            response = self.client.chat.completions.create(
                model=self.settings.deepseek_model,
                temperature=0.7,
                messages=messages,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.warning("DeepSeek dialogue fallback: %s", exc)
            return self._fallback_dialogue_reply(scenario, history, language)

    async def dialogue_hint(
        self,
        scenario: str,
        last_bot_message: str,
        level: str = "Pre-A1",
        language: str = "english",
    ) -> str:
        target = language_info(language)["name_en"]
        user = (
            f"Scenario: {scenario}. Bot said: {last_bot_message}. "
            f"Give one short {level}-level answer hint in Russian and {target}."
        )
        try:
            return self._chat("You help beginners in dialogues.", user, temperature=0.4)
        except Exception:
            return (
                "Попробуй: Ciao! / Привет!"
                if language == "italian"
                else "Try: Hello! / Привет!"
            )

    async def assess_dialogue(
        self,
        scenario: str,
        history: list[dict[str, str]],
        level: str,
        success_criteria: list[str],
        language: str = "english",
    ) -> dict[str, Any]:
        target = language_info(language)["name_en"]
        user_turns = [
            item.get("content", "")
            for item in history
            if item.get("role") == "user"
        ]
        user = (
            f"CEFR level: {level}\n"
            f"Scenario: {scenario}\n"
            f"Success criteria: {json.dumps(success_criteria, ensure_ascii=False)}\n"
            f"Learner messages: {json.dumps(user_turns, ensure_ascii=False)}\n\n"
            "Return JSON only: "
            '{"score":0-100,"feedback_ru":"2-3 useful sentences",'
            '"strengths":["..."],"improvements":["..."],'
            f'"useful_phrases":["{target} — Russian"]}}. '
            "Score communication and completion of the scenario, not perfect grammar."
        )
        try:
            content = self._chat(
                f"You are a fair and practical {target} speaking assessor.",
                user,
                temperature=0.2,
            )
            result = _extract_json(content)
            result["score"] = max(0, min(100, int(result.get("score", 0))))
            return result
        except Exception as exc:
            logger.warning("DeepSeek dialogue assessment fallback: %s", exc)
            english_turns = sum(
                bool(re.search(r"[A-Za-z]{2,}", turn))
                for turn in user_turns
            )
            score = min(100, 40 + english_turns * 12)
            return {
                "score": score,
                "feedback_ru": (
                    "Диалог завершён. Продолжай отвечать полными короткими "
                    "фразами и задавай встречные вопросы."
                ),
                "strengths": ["Ты поддержал(а) разговор."],
                "improvements": ["Добавляй один новый факт в каждую реплику."],
                "useful_phrases": [
                    (
                        "Può ripetere, per favore? — Повторите, пожалуйста."
                        if language == "italian"
                        else "Could you repeat that? — Повторите, пожалуйста."
                    )
                ],
            }

    async def weekly_summary(self, stats: dict[str, Any]) -> str:
        target = language_info(stats.get("learning_language"))["name_en"]
        user = (
            f"Create a short encouraging weekly progress summary in Russian "
            f"for a {target} learner. "
            f"Data: {json.dumps(stats, ensure_ascii=False)}"
        )
        try:
            return self._chat("You are a supportive tutor.", user, temperature=0.5)
        except Exception:
            return (
                f"За неделю ты изучил(а) {stats.get('words_learned', 0)} слов "
                f"и прошёл(ла) {stats.get('lessons_completed', 0)} уроков. Продолжай в том же духе!"
            )

    async def coach_reply(
        self,
        learner_context: dict[str, Any],
        history: list[dict[str, Any]],
        user_message: str,
    ) -> str:
        language = str(learner_context.get("learning_language") or "english")
        target = language_info(language)["name_ru"]
        system = (
            f"Ты персональный наставник по {target} языку для русскоязычного ученика. "
            "Учитывай уровень, цель, прогресс и слабые темы из контекста. "
            f"Поддерживай естественный разговор на русском или на языке «{target}». "
            f"Если ученик пишет на языке «{target}», сначала ответь по смыслу, затем мягко "
            "исправь максимум одну важную ошибку. Не перегружай правилами. "
            "Предлагай один конкретный следующий шаг, когда это уместно. "
            "Не утверждай, что запустил урок или изменил данные — это делает бот. "
            "Ответ должен быть коротким: до 120 слов."
        )
        recent = [
            {
                "role": item.get("role", "user"),
                "content": item.get("content", ""),
            }
            for item in history[-10:]
            if item.get("role") in {"user", "assistant"}
        ]
        messages = [
            {"role": "system", "content": system},
            {
                "role": "system",
                "content": (
                    "Контекст ученика: "
                    + json.dumps(
                        learner_context,
                        ensure_ascii=False,
                        default=str,
                    )
                ),
            },
            *recent,
            {"role": "user", "content": user_message},
        ]
        if not self.client:
            return self._fallback_coach_reply(learner_context, user_message)
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.settings.deepseek_model,
                temperature=0.5,
                messages=messages,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.warning("DeepSeek coach fallback: %s", exc)
            return self._fallback_coach_reply(learner_context, user_message)

    def _fallback_coach_reply(
        self,
        learner_context: dict[str, Any],
        user_message: str,
    ) -> str:
        language = str(learner_context.get("learning_language") or "english")
        target_ru = language_info(language)["name_ru"]
        if re.search(r"[A-Za-z]{3,}", user_message):
            return (
                f"Я понял твою мысль. Продолжай писать по-{target_ru} полными "
                "короткими предложениями — так навык растёт быстрее. "
                "Для следующей практики можно написать: «давай диалог»."
            )
        due = int(learner_context.get("words_due", 0) or 0)
        if due:
            return (
                f"Сейчас лучше начать с повторения: у тебя {due} слов на сегодня. "
                "Напиши «давай слова», и я открою нужный раздел."
            )
        return (
            f"Я рядом как наставник по {target_ru} языку. Можешь задать вопрос, "
            "написать фразу для проверки или попросить: «давай грамматику», "
            "«покажи прогресс» или «что дальше?»."
        )

    def _fallback_reading(
        self,
        topic: str,
        level: str = "Pre-A1",
        language: str = "english",
    ) -> dict[str, Any]:
        if language == "italian":
            return {
                "title": f"Vita quotidiana · {level}",
                "text": (
                    "Luca è uno studente. Vive a Roma con la sua famiglia. "
                    "Gli piacciono il caffè e i libri. Ogni mattina va a scuola a piedi."
                ),
                "keywords": [
                    {"word": "studente", "translation": "студент"},
                    {"word": "famiglia", "translation": "семья"},
                    {"word": "libri", "translation": "книги"},
                    {"word": "a piedi", "translation": "пешком"},
                ],
                "questions": [
                    {
                        "question": "Dove vive Luca?",
                        "options": ["A Roma", "A Milano", "A Napoli"],
                        "correct_index": 0,
                        "explanation_ru": "Лука живёт в Риме.",
                    },
                    {
                        "question": "Con chi vive?",
                        "options": ["Con amici", "Con la famiglia", "Da solo"],
                        "correct_index": 1,
                        "explanation_ru": "Он живёт со своей семьёй.",
                    },
                    {
                        "question": "Che cosa gli piace?",
                        "options": ["Il tè", "Lo sport", "Il caffè e i libri"],
                        "correct_index": 2,
                        "explanation_ru": "Ему нравятся кофе и книги.",
                    },
                    {
                        "question": "Come va a scuola?",
                        "options": ["A piedi", "In autobus", "In treno"],
                        "correct_index": 0,
                        "explanation_ru": "Он ходит в школу пешком.",
                    },
                ],
            }
        return {
            "title": f"{topic.capitalize()} · {level}",
            "text": (
                "Tom is a student (студент). He lives (живёт) in London (в Лондоне). "
                "Tom likes (любит) coffee (кофе) and books (книги)."
            ),
            "keywords": [
                {"word": "student", "translation": "студент"},
                {"word": "lives", "translation": "живёт"},
                {"word": "coffee", "translation": "кофе"},
            ],
            "questions": [
                {
                    "question": "Where does Tom live?",
                    "options": ["In Moscow", "In London", "In Paris"],
                    "correct_index": 1,
                    "explanation_ru": "Tom lives in London.",
                },
                {
                    "question": "What does Tom like?",
                    "options": ["Tea and music", "Coffee and books", "Sports and games"],
                    "correct_index": 1,
                    "explanation_ru": "Tom likes coffee and books.",
                },
                {
                    "question": "What does the word 'student' mean?",
                    "options": ["Студент", "Учитель", "Водитель"],
                    "correct_index": 0,
                    "explanation_ru": "Student переводится как «студент».",
                },
                {
                    "question": "Which statement is true?",
                    "options": [
                        "Tom lives in Paris",
                        "Tom dislikes books",
                        "Tom lives in London",
                    ],
                    "correct_index": 2,
                    "explanation_ru": "В тексте сказано, что Tom lives in London.",
                },
            ],
        }

    def _fallback_listening(
        self,
        level: str,
        topic: str,
        language: str = "english",
    ) -> dict[str, Any]:
        if language == "italian":
            return {
                "title": f"Ascolto: {topic}",
                "transcript": (
                    "Mi chiamo Giulia e vivo a Firenze. Lavoro in un piccolo albergo. "
                    "Comincio alle nove e pranzo con i miei colleghi."
                ),
                "questions": [
                    {
                        "question": "Dove vive Giulia?",
                        "options": ["A Firenze", "A Torino", "A Roma"],
                        "correct_index": 0,
                        "explanation_ru": "Джулия живёт во Флоренции.",
                    },
                    {
                        "question": "Dove lavora?",
                        "options": ["In una scuola", "In un albergo", "In un bar"],
                        "correct_index": 1,
                        "explanation_ru": "Она работает в небольшом отеле.",
                    },
                    {
                        "question": "A che ora comincia?",
                        "options": ["Alle otto", "Alle nove", "Alle dieci"],
                        "correct_index": 1,
                        "explanation_ru": "Она начинает в девять.",
                    },
                ],
            }
        if level == "A2":
            transcript = (
                "Mia planned to take the early train to the city, but it was "
                "cancelled because of bad weather. She waited for the next train "
                "and called her manager to say that she would be late. She arrived "
                "at the office at half past ten."
            )
            details = ("bad weather", "her manager", "half past ten")
        elif level == "A1":
            transcript = (
                "Ben works in a small hotel. He starts at nine in the morning. "
                "Today he is helping a family from Spain. They need a room for "
                "two nights."
            )
            details = ("a small hotel", "at nine", "two nights")
        else:
            transcript = (
                "This is Lucy. She lives in London. She likes tea and books. "
                "Every morning, she walks to work."
            )
            details = ("London", "tea and books", "walks")
        return {
            "title": f"Listening: {topic}",
            "transcript": transcript,
            "questions": [
                {
                    "question": "What is the main topic?",
                    "options": ["A person’s day", "A sports match", "A recipe"],
                    "correct_index": 0,
                    "explanation_ru": "Текст рассказывает о человеке и его ситуации.",
                },
                {
                    "question": "Which detail did you hear first?",
                    "options": [details[0], "a large school", "next Friday"],
                    "correct_index": 0,
                    "explanation_ru": f"В записи звучит: {details[0]}.",
                },
                {
                    "question": "Which other detail is correct?",
                    "options": ["at midnight", details[2], "for five weeks"],
                    "correct_index": 1,
                    "explanation_ru": f"Правильная деталь: {details[2]}.",
                },
            ],
        }

    def _fallback_grammar(
        self,
        topic: str,
        language: str = "english",
    ) -> dict[str, Any]:
        if language == "italian":
            return {
                "explanation_ru": (
                    "Глагол essere («быть»): io sono, tu sei, lui/lei è, "
                    "noi siamo, voi siete, loro sono."
                ),
                "questions": [
                    {
                        "prompt": "Io ___ studente.",
                        "options": ["sono", "sei", "è"],
                        "correct_index": 0,
                        "hint_ru": "После io используется sono.",
                    },
                    {
                        "prompt": "Maria ___ italiana.",
                        "options": ["sei", "è", "siamo"],
                        "correct_index": 1,
                        "hint_ru": "Для Maria используется è.",
                    },
                    {
                        "prompt": "Noi ___ amici.",
                        "options": ["sono", "siete", "siamo"],
                        "correct_index": 2,
                        "hint_ru": "После noi используется siamo.",
                    },
                    {
                        "prompt": "Выбери правильную фразу.",
                        "options": ["Tu sei pronto", "Tu sono pronto", "Tu è pronto"],
                        "correct_index": 0,
                        "hint_ru": "После tu используется sei.",
                    },
                    {
                        "prompt": "Loro ___ a casa.",
                        "options": ["sono", "è", "sei"],
                        "correct_index": 0,
                        "hint_ru": "После loro используется sono.",
                    },
                ],
            }
        exercises = {
            "to be": {
                "explanation_ru": "Глагол to be: I → am, You/We/They → are, He/She/It → is.",
                "questions": [
                    {
                        "prompt": "She ___ a teacher.",
                        "options": ["am", "are", "is"],
                        "correct_index": 2,
                        "hint_ru": "Для she используем is.",
                    },
                    {
                        "prompt": "I ___ ready.",
                        "options": ["am", "is", "are"],
                        "correct_index": 0,
                        "hint_ru": "После I используется am.",
                    },
                    {
                        "prompt": "They ___ at home.",
                        "options": ["is", "are", "am"],
                        "correct_index": 1,
                        "hint_ru": "После they используется are.",
                    },
                    {
                        "prompt": "Choose the correct sentence.",
                        "options": ["We is friends", "We are friends", "We am friends"],
                        "correct_index": 1,
                        "hint_ru": "С we используется форма are.",
                    },
                    {
                        "prompt": "___ he your colleague?",
                        "options": ["Are", "Am", "Is"],
                        "correct_index": 2,
                        "hint_ru": "Вопрос с he начинается с Is.",
                    },
                ],
            }
        }
        return exercises.get(topic.lower(), exercises["to be"])

    def _fallback_writing_check(self, target: str, answer: str) -> dict[str, Any]:
        normalized_target = target.strip().lower()
        normalized_answer = answer.strip().lower()
        if normalized_answer == normalized_target:
            status = "correct"
            feedback = "Отлично! Ответ верный."
        elif normalized_target in normalized_answer or normalized_answer in normalized_target:
            status = "close"
            feedback = f"Почти! Правильно: {target}"
        else:
            status = "incorrect"
            feedback = f"Попробуй ещё. Правильно: {target}"
        return {"status": status, "feedback": feedback, "correct_answer": target}

    def _fallback_dialogue_reply(
        self,
        scenario: str,
        history: list[dict[str, str]],
        language: str = "english",
    ) -> str:
        if language == "italian":
            replies = {
                "introduction": ["Ciao! 👋", "Piacere!", "Come ti chiami?", "A presto! 👋"],
                "coffee": ["Buongiorno! ☕", "Che cosa desidera?", "Piccolo o grande?", "Ecco a Lei!"],
                "ticket": ["Buongiorno! 🎫", "Dove vuole andare?", "Solo andata?", "Buon viaggio!"],
                "small_talk": ["Ciao! 😊", "Bella giornata!", "Ti piace la musica?", "Anche a me!"],
            }
            user_turns = sum(1 for msg in history if msg.get("role") == "user")
            options = replies.get(scenario, replies["introduction"])
            return options[min(user_turns, len(options) - 1)]
        replies = {
            "introduction": ["Hello! 👋", "Nice to meet you! 😊", "What is your name?", "Great! See you soon! 👋"],
            "coffee": ["Hello! ☕", "What would you like?", "Small or large?", "Here you are! Enjoy! 😊"],
            "ticket": ["Hello! 🎫", "Where to?", "One ticket?", "Have a good trip! 🚆"],
            "small_talk": ["Hi! 😊", "Nice weather today!", "Do you like music?", "Me too! Good talk! 👍"],
        }
        user_turns = sum(1 for msg in history if msg.get("role") == "user")
        options = replies.get(scenario, replies["introduction"])
        idx = min(user_turns, len(options) - 1)
        return options[idx]
