from enum import Enum


class ReviewPointStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

    def to_rich_text(self) -> str:
        if self == self.PASSED:
            return f"[green]{self.value}[/green]"
        elif self == self.FAILED:
            return f"[bold bright_red]{self.value}[/bold bright_red]"
        elif self == self.SKIPPED:
            return f"[yellow]{self.value}[/yellow]"
        return ""
