"""CLI entrypoint for Dewey service."""

from __future__ import annotations

import typer
import uvicorn

cli = typer.Typer(help="Dewey service commands")


@cli.command("serve")
def serve(
    host: str = "0.0.0.0",
    port: int = 8920,
    reload: bool = False,
) -> None:
    uvicorn.run(
        "dewey_service.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
