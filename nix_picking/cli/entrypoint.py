import click
from rich.console import Console
from nix_picking.cli.reviewer_handler import ReviewHandler
from nix_picking.cli.rich_repo import ReviewPrintRepo
from rich.live import Live
from rich.spinner import Spinner

console = Console()
spinner = Spinner(
    name=ReviewPrintRepo.get_random_spinner(), text="Working", style="bold green"
)


@click.group()
def cli():
    """CLI for ReviewHandler: Review PRs or Nix files."""
    pass


@cli.command()
@click.argument("pr", type=int)
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
def pr(pr: int, verbose: bool, with_global: bool, additional_parse_levels: int):
    """Review a PR."""
    handler = ReviewHandler(pr=pr)
    with Live(spinner, console=console, refresh_per_second=10) as live:
        result = handler.review(
            withGlobal=with_global, additional_parse_levels=additional_parse_levels
        )
    ReviewPrintRepo.print_review_report(result, console, verbose=verbose)


@cli.command()
@click.argument("nix-file", type=click.Path())
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
def file(
    nix_file: str, verbose: bool, with_global: bool, additional_parse_levels: int
):
    """Review a local Nix file."""
    if not nix_file.endswith(".nix"):
        console.print(f"[bold red]Error: {nix_file} is not a .nix file.")
        return
    try:
        with open(nix_file, "r") as f:
            raw_nix_file = f.read()
    except Exception as e:
        console.print(f"[bold red]Error reading file {nix_file}: {e}")
        return

    handler = ReviewHandler()
    with Live(spinner, console=console, refresh_per_second=10) as live:
        result = handler.review_file(
            raw_nix_file=raw_nix_file,
            withGlobal=with_global,
            additional_parse_levels=additional_parse_levels,
        )
    ReviewPrintRepo.print_review_report(result, console, verbose=verbose)

if __name__ == "__main__":
    cli()
