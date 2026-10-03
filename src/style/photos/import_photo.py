from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, field_validator

from style.photos.library import PhotoLibrary


class ImportPhotoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    original_filename: str

    @field_validator("original_filename")
    @classmethod
    def require_original_filename(cls, value: str) -> str:
        if not value.strip():
            message = "Original filename must not be empty"
            raise ValueError(message)
        return value


@dataclass(frozen=True)
class ImportPhotoResult:
    exported_count: int
    destination: Path


class PhotoNotFoundError(Exception):
    def __init__(self, original_filename: str) -> None:
        super().__init__(f"No photo found with original filename: {original_filename}")


class ImportPhotoUseCase(Protocol):
    def execute(self, original_filename: str) -> ImportPhotoResult: ...


class ImportPhotoService:
    def __init__(self, photo_library: PhotoLibrary, destination: Path) -> None:
        self.photo_library = photo_library
        self.destination = destination

    def execute(self, original_filename: str) -> ImportPhotoResult:
        request = ImportPhotoRequest(original_filename=original_filename)
        exported_count = self.photo_library.export_by_original_filename(
            request.original_filename, self.destination
        )

        if not exported_count:
            raise PhotoNotFoundError(request.original_filename)

        return ImportPhotoResult(exported_count=exported_count, destination=self.destination)
