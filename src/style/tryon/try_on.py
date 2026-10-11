from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, FilePath

from style.tryon.generator import TryOnGenerator

TRY_ON_PROMPT = (
    "The first image is a face photo, the second is a glasses frame. Put that exact frame on "
    "the person in the first image, fitted to their face and head angle. Keep identity, facial "
    "features, facial hair, expression, lighting, background and crop unchanged. Change only "
    "the glasses; add no other accessories and do not retouch the face."
)


class TryOnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    face: FilePath
    frame: FilePath


@dataclass(frozen=True)
class TryOnResult:
    output: Path


class TryOnUseCase(Protocol):
    def execute(self, face: Path, frame: Path) -> TryOnResult: ...


class TryOnService:
    def __init__(self, generator: TryOnGenerator, destination: Path) -> None:
        self.generator = generator
        self.destination = destination

    def execute(self, face: Path, frame: Path) -> TryOnResult:
        request = TryOnRequest(face=face, frame=frame)
        image = self.generator.generate(request.face, request.frame, TRY_ON_PROMPT)

        output = self.destination / f"{request.face.stem}__{request.frame.stem}.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(image)

        return TryOnResult(output=output)
