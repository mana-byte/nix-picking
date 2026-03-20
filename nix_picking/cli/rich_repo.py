from rich.console import Console
from rich.table import Table
from rich.json import JSON

from typing import Any

"""
Reviews from dict has this format:
{
  "local_file.nix": [
    {
      "review_point": "CheckBuildSystem",
      "passed": true,
      "stdout": "",
      "output": null
    },
    {
      "review_point": "CheckHashGitHub",
      "passed": true,
      "stdout": "",
      "output": null
    }
  ]
}
"""


class ReviewPrintRepo:

    @staticmethod
    def get_random_spinner() -> str:
        import random
        spinners = [
            "bouncingBall",
            "point",
            "bouncingBar",
            "dots",
            "line",
            "simpleDotsScrolling",
        ]
        return random.choice(spinners)

    @staticmethod
    def print_review_report(
        review_dict: dict[str, Any], console: Console, verbose: bool = True
    ) -> None:
        for filename, reports in review_dict.items():
            review_table = Table(title=f"Review Report for {filename}", show_lines=True)
            review_table.add_column("Review Point", style="cyan")
            review_table.add_column("PASSED", style="magenta")
            if verbose:
                review_table.add_column("Details", style="green")
            review_table.add_column("Output", style="yellow")
            for report in reports:
                if verbose:
                    review_table.add_row(
                        report["review_point"],
                        "[green]True" if report["passed"] else "[bold bright_red]False",
                        (
                            report["stdout"].strip()
                            if isinstance(report["stdout"], str)
                            else ""
                        ),
                        JSON.from_data(report["output"]) if report["output"] else "",
                    )
                else:
                    review_table.add_row(
                        report["review_point"],
                        "[green]True" if report["passed"] else "[bold bright_red]False",
                        JSON.from_data(report["output"]) if report["output"] else "",
                    )
            console.print(review_table)
