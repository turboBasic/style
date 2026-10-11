from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from style.photos.import_photo import ImportPhotoUseCase, PhotoNotFoundError
from style.tryon.generator import TryOnGenerationError
from style.tryon.try_on import TryOnUseCase


def create_app(
    import_photo_service: ImportPhotoUseCase, try_on_service: TryOnUseCase
) -> typer.Typer:
    app = typer.Typer(no_args_is_help=True)

    @app.callback()
    def main() -> None:
        """Manage photo style data."""

    @app.command()
    def import_photo(
        original_filename: Annotated[
            str, typer.Argument(help="Original filename recorded in the Photos library")
        ],
    ) -> None:
        """Export photos from the Photos library by original filename."""
        try:
            result = import_photo_service.execute(original_filename)
        except ValidationError as error:
            raise typer.BadParameter(str(error), param_hint="original_filename") from error
        except PhotoNotFoundError as error:
            raise typer.BadParameter(str(error), param_hint="original_filename") from error

        typer.echo(f"Exported {result.exported_count} photo(s) to {result.destination}")

    @app.command()
    def try_on(
        face: Annotated[Path, typer.Argument(help="Face photo, e.g. resources/faces/003.jpeg")],
        frame: Annotated[Path, typer.Argument(help="Frame image, e.g. resources/frames/002.jpg")],
    ) -> None:
        """Generate a try-on of a glasses frame on a face photo."""
        try:
            result = try_on_service.execute(face, frame)
        except ValidationError as error:
            raise typer.BadParameter(str(error)) from error
        except TryOnGenerationError as error:
            typer.echo(str(error), err=True)
            raise typer.Exit(1) from error

        typer.echo(f"Saved try-on to {result.output}")

    return app
