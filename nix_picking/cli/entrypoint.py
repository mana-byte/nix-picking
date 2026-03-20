import click
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON
from typing import Any
from nix_picking.cli.reviewer_handler import ReviewHandler
from nix_picking.cli.rich_repo import ReviewPrintRepo

console = Console()


@click.group()
def cli():
    """CLI for ReviewHandler: Review PRs or Nix files."""
    pass


@cli.command()
@click.option("--pr", type=int, required=True, help="PR number to review")
@click.option(
    "--verbose/--no-verbose",
    default=False,
    help="Include stdrout details in review report",
)
@click.option(
    "--with-global/--no-global", default=True, help="Include global context in review"
)
@click.option(
    "--additional-parse-levels",
    type=int,
    default=1,
    help="Additional parse levels for review",
)
def review(pr: int, verbose: bool, with_global: bool, additional_parse_levels: int):
    """Review a PR."""
    handler = ReviewHandler(pr=pr)
    result = handler.review(
        withGlobal=with_global, additional_parse_levels=additional_parse_levels
    )
    ReviewPrintRepo.print_review_report(result, console, verbose=verbose)


@cli.command()
@click.argument("nix-file", type=click.Path(exists=True))
@click.option(
    "--verbose/--no-verbose",
    default=False,
    help="Include stdrout details in review report",
)
@click.option(
    "--with-global/--no-global",
    default=True,
    help="Include global review points in review",
)
@click.option(
    "--additional-parse-levels",
    type=int,
    default=1,
    help="Additional parse levels for review",
)
def review_file(
    nix_file: str, verbose: bool, with_global: bool, additional_parse_levels: int
):
    """Review a Nix file."""
    with open(nix_file, "r") as f:
        raw_nix_file = f.read()
    handler = ReviewHandler()
    result = handler.review_file(
        raw_nix_file=raw_nix_file,
        withGlobal=with_global,
        additional_parse_levels=additional_parse_levels,
    )
    ReviewPrintRepo.print_review_report(result, console, verbose=verbose)


if __name__ == "__main__":
    cli()
