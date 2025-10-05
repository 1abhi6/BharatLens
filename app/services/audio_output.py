from openai import AsyncOpenAI
import tempfile
from app.core.config import settings
import uuid
from app.services import UploadToS3


class AudioOutput:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.s3_obj = UploadToS3()

    async def convert_text_into_audio(self, voice_style: str, assistant_content: str):
        """
        Converts text into audio using OpenAI's TTS model and uploads it to S3.
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            audio_resp = await self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=voice_style,
                input=assistant_content,
            )
        audio_resp.stream_to_file(temp_audio.name)

        # Upload generated audio to S3
        with open(temp_audio.name, "rb") as audio_file:
            audio_url = self.s3_obj.upload_file_to_s3(
                audio_file.read(), f"{uuid.uuid4()}.mp3", "audio/mpeg"
            )

        return audio_url