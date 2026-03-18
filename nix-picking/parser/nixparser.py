from typing import LiteralString
from .enums.builders import Builders


class NixParser:
    """
    A simple parser for simple nix expressions and simple minds.
    """

    def __init__(self, file_path: str):
        self.file_path: str = file_path
        try:
            with open(file_path) as f:
                self.lines: list[str] = f.read().splitlines()
        except FileNotFoundError:
            raise ValueError(f"File not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")

    def locate_builder_args(self) -> int:
        builder = Builders.get_builder_from_file("\n".join(self.lines))
        if not builder:
            raise ValueError("No builder function found in the file.")
        for i, line in enumerate(self.lines):
            if builder.value in line:
                return i
        raise ValueError(
            "Builder function found but could not locate its position in the file."
        )

    def parse_nix_to_dict(
        self, nix_lines: list[LiteralString] | list[str]
    ) -> dict[str, str]:
        """
        Parse lines of a Nix packaging expression. What gets returned is only the top-level keys and values.
        To get nested values, you can call this function recursively on the value of a key.
        This is a naïve parser but should work for simple expressions.
        Args:
            nix_lines: The lines of the args inside the builder function, e.g. the lines inside `meta = { ... }`
        Returns
            A dictionary of the top-level keys and values. The values are still strings and can be parsed further if needed.
        """
        res: dict[str, str] = {}
        current_key: str | None = None
        value_buffer: list[str] = []
        depth: int = 0

        CLOSING_CHARS = {"}", "]", ")"}
        OPENING_CHARS = {"{", "[", "("}

        for line in nix_lines:
            clean_line = line.strip()
            if not clean_line:
                continue

            # check if a new top-level assignment is present (only when not inside a block)
            if depth == 0 and "=" in clean_line:
                key, val = map(str.strip, clean_line.split("=", 1))
                current_key = key
                value_buffer = [val]
            elif current_key:
                value_buffer.append(clean_line)

            # calculate new depth
            depth += sum(clean_line.count(b) for b in OPENING_CHARS)
            depth -= sum(clean_line.count(b) for b in CLOSING_CHARS)

            # Once depth returns to 0 and we have a ; this means we have the full value
            if depth == 0 and current_key and clean_line.endswith(";"):
                res[current_key] = " \n ".join(value_buffer).rstrip(";")
                current_key = None
                value_buffer = []
        return res
