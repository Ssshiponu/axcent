"""
Media types and transcription for multimodal agent interactions.

This module provides:
- Media classes (Image, Audio) for handling media content
- Transcriber class for converting media to text descriptions
"""

import base64
import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .llm import LLMBackend

MediaType = Literal["image", "audio"]


@dataclass
class Media:
    """
    Base class for media content.
    
    Media can be loaded from a local file path or referenced by URL.
    """
    type: MediaType
    mime_type: str = ""
    data: Optional[bytes] = field(default=None, repr=False)
    url: Optional[str] = None
    
    @classmethod
    def from_file(cls, path: str, media_type: MediaType) -> "Media":
        """Load media from a local file path."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Media file not found: {path}")
        
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = "image/jpeg" if media_type == "image" else "audio/mp3"
        
        with open(file_path, "rb") as f:
            data = f.read()
        
        return cls(type=media_type, mime_type=mime_type, data=data)
    
    @classmethod
    def from_url(cls, url: str, media_type: MediaType, mime_type: Optional[str] = None) -> "Media":
        """Create media reference from URL."""
        if mime_type is None:
            guessed_type, _ = mimetypes.guess_type(url)
            mime_type = guessed_type or ("image/jpeg" if media_type == "image" else "audio/mp3")
        
        return cls(type=media_type, mime_type=mime_type, url=url)
    
    def to_base64(self) -> str:
        """Return base64-encoded data."""
        if self.data is None:
            raise ValueError("No data available. Media was created from URL only.")
        return base64.b64encode(self.data).decode("utf-8")
    
    def to_data_uri(self) -> str:
        """Return data URI for embedding."""
        return f"data:{self.mime_type};base64,{self.to_base64()}"


class Image(Media):
    """Image media type for vision capabilities."""
    
    def __init__(self, path: Optional[str] = None, url: Optional[str] = None):
        if path and url:
            raise ValueError("Provide either path or url, not both.")
        if not path and not url:
            raise ValueError("Provide either path or url.")
        
        if path:
            media = Media.from_file(path, "image")
            super().__init__(type="image", mime_type=media.mime_type, data=media.data, url=None)
        else:
            assert url is not None
            media = Media.from_url(url, "image")
            super().__init__(type="image", mime_type=media.mime_type, data=None, url=url)


class Audio(Media):
    """Audio media type for audio understanding capabilities."""
    
    def __init__(self, path: Optional[str] = None, url: Optional[str] = None):
        if path and url:
            raise ValueError("Provide either path or url, not both.")
        if not path and not url:
            raise ValueError("Provide either path or url.")
        
        if path:
            media = Media.from_file(path, "audio")
            super().__init__(type="audio", mime_type=media.mime_type, data=media.data, url=None)
        else:
            assert url is not None
            media = Media.from_url(url, "audio")
            super().__init__(type="audio", mime_type=media.mime_type, data=None, url=url)


class Transcriber:
    """
    Transcribes media (images/audio) to text using an LLM backend.
    
    Example:
        transcriber = Transcriber(
            system_prompt="Describe the image briefly.",
            backend=GeminiBackend()
        )
        text = transcriber.transcribe("https://example.com/image.jpg")
    """
    
    def __init__(
        self, 
        system_prompt: str = "Describe the media content accurately and concisely.",
        backend: Optional["LLMBackend"] = None,
        model: Optional[str] = None
    ):
        """
        Initialize the Transcriber.
        
        Args:
            system_prompt: Instructions for how to transcribe/describe the media.
            backend: LLM backend to use. If None, uses GeminiBackend (recommended for media).
            model: Model name to use. If None, uses backend default.
        """
        self.system_prompt = system_prompt
        
        if backend is None:
            from .llm import GeminiBackend
            self.backend = GeminiBackend(model=model) if model else GeminiBackend()
        else:
            self.backend = backend
    
    def _detect_media_type(self, url: str) -> MediaType:
        """Detect media type from URL extension."""
        mime_type, _ = mimetypes.guess_type(url)
        if mime_type:
            if mime_type.startswith("audio"):
                return "audio"
        return "image"  # Default to image
    
    def transcribe(self, url: str) -> str:
        """
        Transcribe media from a URL to text.
        
        Args:
            url: URL to the media file (image or audio).
            
        Returns:
            Text description/transcription of the media.
        """
        media_type = self._detect_media_type(url)
        
        # Build message with media content
        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please transcribe/describe this media:"},
                    {
                        "type": "image_url",
                        "image_url": {"url": url}
                    } if media_type == "image" else {
                        "type": "input_audio",
                        "input_audio": {"url": url, "format": "mp3"}
                    }
                ]
            }
        ]
        
        response = self.backend.chat(messages, tools=None)
        return response.choices[0].message.content or ""
    
    def transcribe_file(self, path: str) -> str:
        """
        Transcribe media from a local file to text.
        
        Args:
            path: Path to the local media file.
            
        Returns:
            Text description/transcription of the media.
        """
        mime_type, _ = mimetypes.guess_type(path)
        media_type: MediaType = "audio" if mime_type and mime_type.startswith("audio") else "image"
        
        if media_type == "image":
            media = Image(path=path)
        else:
            media = Audio(path=path)
        
        # Build message with inline media
        if media.data:
            data_uri = media.to_data_uri()
            content_part = {
                "type": "image_url",
                "image_url": {"url": data_uri}
            } if media_type == "image" else {
                "type": "input_audio", 
                "input_audio": {"data": media.to_base64(), "format": media.mime_type.split("/")[-1]}
            }
        else:
            raise ValueError("Cannot transcribe file without data")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please transcribe/describe this media:"},
                    content_part
                ]
            }
        ]
        
        response = self.backend.chat(messages, tools=None)
        return response.choices[0].message.content or ""
