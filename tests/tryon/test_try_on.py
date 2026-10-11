import base64
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from style.tryon.gemini import GeminiImageTryOnGenerator
from style.tryon.generator import TryOnGenerationError
from style.tryon.openai import OpenAIImageTryOnGenerator
from style.tryon.openrouter import OpenRouterImageTryOnGenerator
from style.tryon.try_on import TRY_ON_PROMPT, TryOnService


class FakeTryOnGenerator:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, Path, str]] = []

    def generate(self, face: Path, frame: Path, prompt: str) -> bytes:
        self.calls.append((face, frame, prompt))
        return b"png-bytes"


def test_try_on_writes_output_named_after_face_and_frame(tmp_path: Path) -> None:
    face = tmp_path / "003-face.jpeg"
    frame = tmp_path / "002-frame.jpg"
    face.write_bytes(b"face")
    frame.write_bytes(b"frame")
    generator = FakeTryOnGenerator()

    result = TryOnService(generator, tmp_path / "try-ons").execute(face, frame)

    assert result.output == tmp_path / "try-ons" / "003-face__002-frame.png"
    assert result.output.read_bytes() == b"png-bytes"
    assert generator.calls == [(face, frame, TRY_ON_PROMPT)]


def test_try_on_rejects_missing_input(tmp_path: Path) -> None:
    service = TryOnService(FakeTryOnGenerator(), tmp_path)

    with pytest.raises(ValidationError):
        service.execute(tmp_path / "missing.jpeg", tmp_path / "missing.jpg")


def test_openai_generator_posts_both_images_and_decodes_result(tmp_path: Path) -> None:
    face = tmp_path / "face.jpeg"
    frame = tmp_path / "frame.png"
    face.write_bytes(b"face")
    frame.write_bytes(b"frame")
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(b"out").decode()}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    generator = OpenAIImageTryOnGenerator("key", client=client)

    assert generator.generate(face, frame, "prompt") == b"out"
    assert seen[0].headers["authorization"] == "Bearer key"
    assert seen[0].content.count(b'name="image[]"') == 2


def test_openai_generator_wraps_http_errors(tmp_path: Path) -> None:
    face = tmp_path / "face.jpeg"
    face.write_bytes(b"face")
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(401, text="bad key"))
    )
    generator = OpenAIImageTryOnGenerator("key", client=client)

    with pytest.raises(TryOnGenerationError, match=r"401.*bad key"):
        generator.generate(face, face, "prompt")


def test_gemini_generator_posts_images_and_decodes_last_image(tmp_path: Path) -> None:
    face = tmp_path / "face.jpeg"
    face.write_bytes(b"face")
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        steps = [
            {"type": "model_output", "content": [{"type": "text", "text": "done"}]},
            {
                "type": "model_output",
                "content": [{"type": "image", "data": base64.b64encode(b"out").decode()}],
            },
        ]
        return httpx.Response(200, json={"steps": steps})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    generator = GeminiImageTryOnGenerator("key", client=client)

    assert generator.generate(face, face, "prompt") == b"out"
    assert seen[0].headers["x-goog-api-key"] == "key"
    assert seen[0].content.count(b'"mime_type"') == 2


def test_gemini_generator_reports_missing_image(tmp_path: Path) -> None:
    face = tmp_path / "face.jpeg"
    face.write_bytes(b"face")
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"steps": []}))
    )
    generator = GeminiImageTryOnGenerator("key", client=client)

    with pytest.raises(TryOnGenerationError, match="no image"):
        generator.generate(face, face, "prompt")


def test_openrouter_generator_sends_data_url_references(tmp_path: Path) -> None:
    face = tmp_path / "face.jpeg"
    face.write_bytes(b"face")
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(b"out").decode()}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    generator = OpenRouterImageTryOnGenerator("key", client=client)

    assert generator.generate(face, face, "prompt") == b"out"
    assert seen[0].headers["authorization"] == "Bearer key"
    assert seen[0].content.count(b"data:image/jpeg;base64,") == 2
