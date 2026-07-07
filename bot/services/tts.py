import logging
import uuid
from pathlib import Path

import httpx
from gtts import gTTS

from bot.config import AUDIO_DIR

logger = logging.getLogger(__name__)


class TTSService:
    def __init__(self) -> None:
        self.audio_dir = AUDIO_DIR
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    async def synthesize(self, text: str, lang: str = "en") -> Path | None:
        filename = self.audio_dir / f"{uuid.uuid4().hex}.mp3"
        try:
            tts = gTTS(text=text, lang=lang)
            tts.save(str(filename))
            return filename
        except Exception as exc:
            logger.warning("gTTS failed: %s", exc)
            return None

    async def from_dictionary_audio(self, audio_url: str) -> Path | None:
        if not audio_url:
            return None
        filename = self.audio_dir / f"{uuid.uuid4().hex}.mp3"
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(audio_url)
                if response.status_code != 200:
                    return None
                filename.write_bytes(response.content)
                return filename
        except Exception as exc:
            logger.warning("Dictionary audio download failed: %s", exc)
            return None

    async def get_word_audio(self, word: str, audio_url: str = "") -> Path | None:
        path = await self.from_dictionary_audio(audio_url)
        if path:
            return path
        return await self.synthesize(word)
