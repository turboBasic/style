from pathlib import Path
from typing import Protocol


class TryOnGenerationError(Exception):
    pass


class TryOnGenerator(Protocol):
    def generate(self, face: Path, frame: Path, prompt: str) -> bytes: ...
