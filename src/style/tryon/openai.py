import base64
import mimetypes
from pathlib import Path

import httpx
from pydantic import BaseModel, Field, ValidationError

from style.tryon.generator import TryOnGenerationError

API_URL = "https://api.openai.com/v1/images/edits"
DEFAULT_MODEL = "gpt-image-1"
TIMEOUT_SECONDS = 300.0


class ImageData(BaseModel):
    b64_json: str


class ImageEditResponse(BaseModel):
    data: list[ImageData] = Field(min_length=1)


class OpenAIImageTryOnGenerator:
    def __init__(
        self, api_key: str, *, model: str = DEFAULT_MODEL, client: httpx.Client | None = None
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.client = client or httpx.Client(timeout=TIMEOUT_SECONDS)

    def generate(self, face: Path, frame: Path, prompt: str) -> bytes:
        files = [
            (
                "image[]",
                (path.name, path.read_bytes(), mimetypes.guess_type(path)[0] or "image/jpeg"),
            )
            for path in (face, frame)
        ]
        try:
            response = self.client.post(
                API_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={"model": self.model, "prompt": prompt, "input_fidelity": "high"},
                files=files,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            message = (
                f"OpenAI image edit failed ({error.response.status_code}): {error.response.text}"
            )
            raise TryOnGenerationError(message) from error
        except httpx.HTTPError as error:
            raise TryOnGenerationError(f"OpenAI image edit failed: {error}") from error

        try:
            parsed = ImageEditResponse.model_validate_json(response.content)
        except ValidationError as error:
            raise TryOnGenerationError(f"Unexpected OpenAI response: {error}") from error
        return base64.b64decode(parsed.data[0].b64_json)
