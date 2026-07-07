import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DICTIONARY_API = "https://api.dictionaryapi.dev/api/v2/entries/en"


class DictionaryService:
    async def lookup(self, word: str) -> dict[str, Any]:
        word = word.strip().lower()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{DICTIONARY_API}/{word}")
                if response.status_code != 200:
                    return self._fallback(word)
                data = response.json()
                if not data:
                    return self._fallback(word)
                entry = data[0]
                phonetic = entry.get("phonetic", "")
                audio = ""
                for ph in entry.get("phonetics", []):
                    if ph.get("audio"):
                        audio = ph["audio"]
                        break
                definition = ""
                example = ""
                meanings = entry.get("meanings", [])
                if meanings:
                    defs = meanings[0].get("definitions", [])
                    if defs:
                        definition = defs[0].get("definition", "")
                        example = defs[0].get("example", "") or ""
                return {
                    "word": word,
                    "phonetic": phonetic,
                    "audio_url": audio,
                    "definition": definition,
                    "example": example,
                }
        except Exception as exc:
            logger.warning("Dictionary API fallback for %s: %s", word, exc)
            return self._fallback(word)

    def _fallback(self, word: str) -> dict[str, Any]:
        return {
            "word": word,
            "phonetic": "",
            "audio_url": "",
            "definition": "",
            "example": "",
        }
