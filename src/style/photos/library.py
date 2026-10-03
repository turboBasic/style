from pathlib import Path
from typing import Protocol


class PhotoLibrary(Protocol):
    def export_by_original_filename(self, original_filename: str, destination: Path) -> int: ...
