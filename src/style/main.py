import os
from pathlib import Path

from style.cli import create_app
from style.photos.import_photo import ImportPhotoService
from style.photos.osxphotos import OsxPhotosPhotoLibrary
from style.tryon.gemini import GeminiImageTryOnGenerator
from style.tryon.generator import TryOnGenerator
from style.tryon.openai import OpenAIImageTryOnGenerator
from style.tryon.openrouter import DEFAULT_MODEL, OpenRouterImageTryOnGenerator
from style.tryon.try_on import TryOnService


def build_try_on_generator() -> TryOnGenerator:
    if "OPENROUTER_API_KEY" in os.environ:
        return OpenRouterImageTryOnGenerator(
            os.environ["OPENROUTER_API_KEY"],
            model=os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL),
        )
    if "GEMINI_API_KEY" in os.environ:
        return GeminiImageTryOnGenerator(os.environ["GEMINI_API_KEY"])
    return OpenAIImageTryOnGenerator(os.environ.get("OPENAI_API_KEY", ""))


app = create_app(
    ImportPhotoService(OsxPhotosPhotoLibrary(), Path("resources/faces")),
    TryOnService(build_try_on_generator(), Path("resources/try-ons")),
)
