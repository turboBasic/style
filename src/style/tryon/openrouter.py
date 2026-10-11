import base64
import mimetypes
from pathlib import Path

import httpx
from pydantic import BaseModel, Field, ValidationError

from style.tryon.generator import TryOnGenerationError

API_URL = "https://openrouter.ai/api/v1/images"
DEFAULT_MODEL = "openai/gpt-image-1"
TIMEOUT_SECONDS = 300.0


class ImageData(BaseModel):
    b64_json: str


class ImagesResponse(BaseModel):
    data: list[ImageData] = Field(min_length=1)


class OpenRouterImageTryOnGenerator:
    def __init__(
        self, api_key: str, *, model: str = DEFAULT_MODEL, client: httpx.Client | None = None
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.client = client or httpx.Client(timeout=TIMEOUT_SECONDS)

    def generate(self, face: Path, frame: Path, prompt: str) -> bytes:
        references = [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mimetypes.guess_type(path)[0] or 'image/jpeg'};base64,"
                    f"{base64.b64encode(path.read_bytes()).decode()}"
                },
            }
            for path in (face, frame)
        ]
        body = {"model": self.model, "prompt": prompt, "input_references": references}
        try:
            response = self.client.post(
                API_URL, headers={"Authorization": f"Bearer {self.api_key}"}, json=body
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            message = (
                f"OpenRouter image edit failed ({error.response.status_code}): "
                f"{error.response.text}"
            )
            raise TryOnGenerationError(message) from error
        except httpx.HTTPError as error:
            raise TryOnGenerationError(f"OpenRouter image edit failed: {error}") from error

        try:
            parsed = ImagesResponse.model_validate_json(response.content)
        except ValidationError as error:
            raise TryOnGenerationError(f"Unexpected OpenRouter response: {error}") from error
        return base64.b64decode(parsed.data[0].b64_json)
