"""
OpenAI service integration
"""
import io
import logging
import asyncio
import os
import time
import base64
import requests
from typing import Optional, Dict, Any, List
from openai import OpenAI
from openai.types.responses.response import Response

logger = logging.getLogger(__name__)

IMAGE_GENERATION_MODEL = "gpt-image-2"


class OpenAIService:
    """Service for OpenAI API interactions"""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required")
        self.client = OpenAI(api_key=api_key)

    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.client is not None

    async def transcribe_audio(self, voice_file: bytes) -> Optional[str]:
        """
        Transcribe audio using Whisper API

        Args:
            voice_file: Audio file as bytes

        Returns:
            Transcribed text or None if error
        """
        if not self.client:
            logger.error("OpenAI client not available for transcription")
            return None

        try:
            voice_file_obj = io.BytesIO(voice_file)
            voice_file_obj.name = "voice.ogg"
            voice_file_obj.seek(0)

            def _transcribe():
                return self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=voice_file_obj,
                    response_format="text"
                )

            transcription = await asyncio.to_thread(_transcribe)

            if hasattr(transcription, 'text'):
                return transcription.text
            if isinstance(transcription, dict) and 'text' in transcription:
                return transcription['text']
            return str(transcription)

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            error_msg = str(e)
            if "Unrecognized file format" in error_msg:
                logger.error(
                    "❌ **Error de formato de archivo**\n\n"
                    "El formato del audio no es compatible con Whisper. "
                    "Intenta enviar el audio en un formato diferente o como documento de audio."
                )
            return None

    def create_response(
        self,
        input_data: str | List[Dict[str, Any]] | None = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        model: str = "gpt-4.1-mini",
        instructions: Optional[str] = None,
        store: bool = True,
        previous_response_id: Optional[str] = None,
    ) -> Response | None:
        """
        Create response with OpenAI Responses API

        Args:
            input_data: Input string or list of messages for the conversation
            tools: List of tools/functions available
            model: Model to use (optional)
            instructions: System instructions
            store: Whether to store the response
            previous_response_id: Previous response ID for chaining

        Returns:
            OpenAI response or None if error
        """
        if not self.client:
            logger.error("OpenAI client not available")
            return None

        model_to_use = model or "gpt-4.1-mini"

        try:
            logger.debug(f"Creating response (model={model_to_use})")

            response = self.client.responses.create(
                    model=model_to_use,
                    tools=tools,
                    instructions=instructions,
                    store=store,
                    input=input_data,
                    previous_response_id=previous_response_id
                )
            return response

        except Exception as e:
            logger.error(f"Error in response creation: {e}")
            return None

    def generate_image(self, prompt: str, n: int = 1, size: str = "1024x1024", output_dir: Optional[str] = None) -> Optional[List[str]]:
        """
        Generate images from a text prompt using OpenAI Images API.

        Args:
            prompt: Text prompt to generate the image.
            n: Number of images to generate.
            size: Image size (e.g. '256x256', '512x512', '1024x1024').
            output_dir: Directory path to save generated images. If None, saves in cwd.

        Returns:
            List of saved file paths or None on error.
        """
        if not self.client:
            logger.error("OpenAI client not available for image generation")
            return None

        try:
            resp = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=n,
                size=size
            )

            data = None
            if hasattr(resp, 'data'):
                data = resp.data
            elif isinstance(resp, dict) and 'data' in resp:
                data = resp['data']
            else:
                data = []

            saved_paths: List[str] = []
            timestamp = int(time.time())
            target_dir = output_dir or os.getcwd()
            if output_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)

            for i, item in enumerate(data):
                if hasattr(item, 'url'):
                    url = item.url
                    response = requests.get(url)
                    if response.status_code == 200:
                        filename = f"generated_{timestamp}_{i+1}.png"
                        filepath = os.path.join(target_dir, filename)
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        saved_paths.append(filepath)
                else:
                    b64 = None
                    if isinstance(item, dict):
                        b64 = item.get('b64_json') or item.get('b64')
                    else:
                        b64 = getattr(item, 'b64_json', None) or getattr(item, 'b64', None)

                    if not b64:
                        logger.warning(f"No base64 content for image #{i}")
                        continue

                    image_bytes = base64.b64decode(b64)
                    filename = f"generated_{timestamp}_{i+1}.png"
                    filepath = os.path.join(target_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(image_bytes)
                    saved_paths.append(filepath)

            return saved_paths

        except Exception as e:
            logger.error(f"Error generating images: {e}")
            return None

    def generate_image_artifacts(
        self,
        *,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "auto",
        background: str = "auto",
        output_format: str = "png",
    ) -> dict[str, Any]:
        """Generate a single image and return decoded bytes plus response metadata."""
        if not self.client:
            raise RuntimeError("OpenAI client not available for image generation")

        resp = self.client.images.generate(
            model=IMAGE_GENERATION_MODEL,
            prompt=prompt,
            n=1,
            size=size,
            quality=quality,
            background=background,
            output_format=output_format,
        )
        data = getattr(resp, "data", None)
        if not data and isinstance(resp, dict):
            data = resp.get("data")
        if not data:
            raise RuntimeError("OpenAI image generation returned no image data")

        item = data[0]
        b64 = (
            item.get("b64_json")
            if isinstance(item, dict)
            else getattr(item, "b64_json", None)
        )
        url = item.get("url") if isinstance(item, dict) else getattr(item, "url", None)
        if b64:
            image_bytes = base64.b64decode(b64)
        elif url:
            image_resp = requests.get(url, timeout=30)
            image_resp.raise_for_status()
            image_bytes = image_resp.content
        else:
            raise RuntimeError("OpenAI image generation returned neither b64_json nor url")

        revised_prompt = (
            item.get("revised_prompt")
            if isinstance(item, dict)
            else getattr(item, "revised_prompt", None)
        )
        usage = getattr(resp, "usage", None)
        if hasattr(usage, "model_dump"):
            usage = usage.model_dump(mode="json")

        def _response_value(key: str, default: Any = None) -> Any:
            if isinstance(resp, dict):
                return resp.get(key, default)
            return getattr(resp, key, default)

        return {
            "bytes": image_bytes,
            "model": IMAGE_GENERATION_MODEL,
            "prompt": prompt,
            "revised_prompt": revised_prompt,
            "size": _response_value("size", size) or size,
            "quality": _response_value("quality", quality) or quality,
            "background": _response_value("background", background) or background,
            "output_format": _response_value("output_format", output_format) or output_format,
            "created": _response_value("created"),
            "usage": usage if isinstance(usage, dict) else None,
        }

    def generate_profile_avatar(self, user_description: str, output_dir: Optional[str] = None) -> Optional[str]:
        """
        Generate a profile avatar image for a user based on their description.

        Args:
            user_description: Description of the user for avatar generation.
            output_dir: Directory path to save the generated image. If None, saves in cwd.

        Returns:
            Path to saved image file or None on error.
        """
        if not self.client:
            logger.error("OpenAI client not available for image generation")
            return None

        # Create a more specific prompt for profile avatars
        prompt = f"Professional profile avatar portrait of a person: {user_description}. Clean, modern, professional headshot style, suitable for a profile picture, high quality, detailed, realistic"
        
        try:
            resp = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )

            data = None
            if hasattr(resp, 'data'):
                data = resp.data
            elif isinstance(resp, dict) and 'data' in resp:
                data = resp['data']
            else:
                data = []

            if not data or len(data) == 0:
                logger.error("No image data received from OpenAI")
                return None

            # Save the first (and only) image
            item = data[0]
            timestamp = int(time.time())
            target_dir = output_dir or os.getcwd()
            if output_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)

            if hasattr(item, 'url'):
                url = item.url
                response = requests.get(url)
                if response.status_code == 200:
                    filename = f"profile_avatar_{timestamp}.png"
                    filepath = os.path.join(target_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    return filepath
            else:
                b64 = None
                if isinstance(item, dict):
                    b64 = item.get('b64_json') or item.get('b64')
                else:
                    b64 = getattr(item, 'b64_json', None) or getattr(item, 'b64', None)

                if not b64:
                    logger.error("No base64 content for generated image")
                    return None

                image_bytes = base64.b64decode(b64)
                filename = f"profile_avatar_{timestamp}.png"
                filepath = os.path.join(target_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
                return filepath

        except Exception as e:
            logger.error(f"Error generating profile avatar: {e}")
            return None

    async def generate_speech(
        self,
        text: str,
        voice: str = "alloy",
        audio_format: str = "mp3",
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate speech (TTS) from text using OpenAI's audio/speech API and save it as a file.

        Args:
            text: Text to synthesize.
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer).
            audio_format: Output audio format (mp3, opus, aac, flac, wav, pcm).
            output_path: Path to save the generated audio. If None, saves in cwd.

        Returns:
            Path to saved audio file or None on error.
        """
        if not self.client:
            logger.error("OpenAI client not available for speech generation")
            return None

        try:
            def _generate_tts():
                return self.client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text,
                    response_format=audio_format
                )

            resp = await asyncio.to_thread(_generate_tts)

            if hasattr(resp, 'content'):
                audio_bytes = resp.content
            elif isinstance(resp, bytes):
                audio_bytes = resp
            else:
                logger.error("Could not extract audio bytes from TTS response")
                return None

            timestamp = int(time.time())
            if output_path:
                _, ext = os.path.splitext(output_path)
                if ext:
                    filepath = output_path
                    dirpath = os.path.dirname(filepath) or os.getcwd()
                    os.makedirs(dirpath, exist_ok=True)
                else:
                    os.makedirs(output_path, exist_ok=True)
                    filepath = os.path.join(output_path, f"speech_{timestamp}.{audio_format}")
            else:
                filepath = os.path.join(os.getcwd(), f"speech_{timestamp}.{audio_format}")

            with open(filepath, "wb") as f:
                f.write(audio_bytes)

            return filepath

        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return None