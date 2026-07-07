import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

TATOEBA_API = "https://tatoeba.org/en/api_v0/search"


class TatoebaService:
    async def get_examples(self, word: str, limit: int = 2) -> list[dict[str, str]]:
        params = {
            "query": word,
            "from": "eng",
            "to": "rus",
            "orphans": "no",
            "sort": "relevance",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(TATOEBA_API, params=params)
                if response.status_code != 200:
                    return self._fallback(word)
                payload = response.json()
                results = []
                for item in payload.get("results", [])[:limit]:
                    text = item.get("text", "")
                    translation = ""
                    transcriptions = item.get("translations", [])
                    if transcriptions:
                        translation = transcriptions[0].get("text", "")
                    if text:
                        results.append({"en": text, "ru": translation})
                return results or self._fallback(word)
        except Exception as exc:
            logger.warning("Tatoeba fallback for %s: %s", word, exc)
            return self._fallback(word)

    def _fallback(self, word: str) -> list[dict[str, str]]:
        return [{"en": f"I like {word}.", "ru": f"Мне нравится {word}."}]
