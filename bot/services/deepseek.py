import json
import logging
import re
from pathlib import Path
from typing import Any

import openai

from bot.config import PROMPTS_DIR, Settings

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

    async def generate_reading_lesson(self, topic: str, level: str = "Pre-A1") -> dict[str, Any]:
        system = _load_prompt("exercises.txt") or (
            "You are a friendly English tutor for Russian-speaking beginners."
        )
        user = (
            f"Create a Pre-A1 reading lesson about '{topic}'.\n"
            "Return JSON with keys: title, text (English with Russian translations in brackets), "
            "keywords (list of {word, translation}), questions (list of "
            "{question, options[3], correct_index, explanation_ru})."
        )
        try:
            content = self._chat(system, user, temperature=0.3)
            return _extract_json(content)
        except Exception as exc:
            logger.warning("DeepSeek reading fallback: %s", exc)
            return self._fallback_reading(topic)

    async def generate_grammar_exercise(self, topic: str, level: str = "Pre-A1") -> dict[str, Any]:
        system = _load_prompt("exercises.txt") or "You are an English grammar tutor."
        user = (
            f"Create a grammar lesson on '{topic}' for level {level}.\n"
            "Return JSON: explanation_ru, questions (list of "
            "{prompt, options[3], correct_index, hint_ru})."
        )
        try:
            content = self._chat(system, user, temperature=0.3)
            return _extract_json(content)
        except Exception as exc:
            logger.warning("DeepSeek grammar fallback: %s", exc)
            return self._fallback_grammar(topic)

    async def check_writing_answer(
        self,
        target_phrase: str,
        user_answer: str,
        level: str = "Pre-A1",
    ) -> dict[str, Any]:
        system = _load_prompt("feedback.txt") or "Evaluate beginner English answers gently."
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

    async def dialogue_reply(
        self,
        scenario: str,
        role: str,
        history: list[dict[str, str]],
        level: str = "Pre-A1",
    ) -> str:
        system = _load_prompt("dialogues.txt") or "You are a friendly dialogue partner."
        system = system.format(role=role, scenario=scenario, level=level)
        messages = [{"role": "system", "content": system}]
        messages.extend(history)
        if not self.client:
            return self._fallback_dialogue_reply(scenario, history)
        try:
            response = self.client.chat.completions.create(
                model=self.settings.deepseek_model,
                temperature=0.7,
                messages=messages,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.warning("DeepSeek dialogue fallback: %s", exc)
            return self._fallback_dialogue_reply(scenario, history)

    async def dialogue_hint(self, scenario: str, last_bot_message: str) -> str:
        user = (
            f"Scenario: {scenario}. Bot said: {last_bot_message}. "
            "Give one short A1-level answer hint in Russian and English."
        )
        try:
            return self._chat("You help beginners in dialogues.", user, temperature=0.4)
        except Exception:
            return "Try: Hello! / Привет!"

    async def weekly_summary(self, stats: dict[str, Any]) -> str:
        user = (
            "Create a short encouraging weekly progress summary in Russian for an English learner. "
            f"Data: {json.dumps(stats, ensure_ascii=False)}"
        )
        try:
            return self._chat("You are a supportive tutor.", user, temperature=0.5)
        except Exception:
            return (
                f"За неделю ты изучил(а) {stats.get('words_learned', 0)} слов "
                f"и прошёл(ла) {stats.get('lessons_completed', 0)} уроков. Продолжай в том же духе!"
            )

    def _fallback_reading(self, topic: str) -> dict[str, Any]:
        return {
            "title": topic.capitalize(),
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
            ],
        }

    def _fallback_grammar(self, topic: str) -> dict[str, Any]:
        exercises = {
            "to be": {
                "explanation_ru": "Глагол to be: I → am, You/We/They → are, He/She/It → is.",
                "questions": [
                    {
                        "prompt": "She ___ a teacher.",
                        "options": ["am", "are", "is"],
                        "correct_index": 2,
                        "hint_ru": "Для she используем is.",
                    }
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

    def _fallback_dialogue_reply(self, scenario: str, history: list[dict[str, str]]) -> str:
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
