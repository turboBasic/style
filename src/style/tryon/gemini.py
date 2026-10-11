import base64
import mimetypes
from pathlib import Path

import httpx
from pydantic import BaseModel, ValidationError

from style.tryon.generator import TryOnGenerationError

API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_MODEL = "gemini-nano-banana-2.1"
TIMEOUT_SECONDS = 300.0


class Content(BaseModel):
    type: str
    data: str | None = None


class Step(BaseModel):
    type: str
    content: list[Content] = []


class InteractionResponse(BaseModel):
    steps: list[Step] = []


class GeminiImageTryOnGenerator:
    def __init__(
        self, api_key: str, *, model: str = DEFAULT_MODEL, client: httpx.Client | None = None
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.client = client or httpx.Client(timeout=TIMEOUT_SECONDS)

    def generate(self, face: Path, frame: Path, prompt: str) -> bytes:
        images = [
            {
                "type": "image",
                "mime_type": mimetypes.guess_type(path)[0] or "image/jpeg",
                "data": base64.b64encode(path.read_bytes()).decode(),
            }
            for path in (face, frame)
        ]
        body = {
            "model": self.model,
            "input": [{"type": "text", "text": prompt}, *images],
            "response_format": {"type": "image"},
        }
        try:
            response = self.client.post(
                API_URL, headers={"x-goog-api-key": self.api_key}, json=body
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            message = (
                f"Gemini image edit failed ({error.response.status_code}): {error.response.text}"
            )
            raise TryOnGenerationError(message) from error
        except httpx.HTTPError as error:
            raise TryOnGenerationError(f"Gemini image edit failed: {error}") from error

        try:
            parsed = InteractionResponse.model_validate_json(response.content)
        except ValidationError as error:
            raise TryOnGenerationError(f"Unexpected Gemini response: {error}") from error

        data = [
            block.data
            for step in parsed.steps
            if step.type == "model_output"
            for block in step.content
            if block.type == "image" and block.data
        ]
        if not data:
            raise TryOnGenerationError("Gemini response contained no image")
        return base64.b64decode(data[-1])
