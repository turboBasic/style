from typing import Annotated

import typer
from pydantic import ValidationError

from style.photos.import_photo import ImportPhotoUseCase, PhotoNotFoundError


def create_app(import_photo_service: ImportPhotoUseCase) -> typer.Typer:
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

    return app
