import json
from pathlib import Path
from typing import Any, Union
from .enums.builders import Builders


class NixParser:
    """
    A simple parser for simple nix expressions and simple minds.
    """

    OPENING_CHARS: set[str] = {"{", "[", "("}
    CLOSING_CHARS: set[str] = {"}", "]", ")"}

    def __init__(self, file_path: str):
        self.file_path = file_path
        if not file_path:
            return
        path = Path(file_path)
        if not path.is_file():
            raise ValueError(f"File not found: {file_path}")
        try:
            self.lines: list[str] = path.read_text().splitlines()
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")

    def locate_builder_args(self) -> int:
        builder = Builders.get_builder_from_file("\n".join(self.lines))
        if not builder:
            raise ValueError("No builder function found in the file.")

        # Optimize: Search backwards to find the last occurrence efficiently
        for i in range(len(self.lines) - 1, -1, -1):
            if builder.value in self.lines[i]:
                return i + 1

        raise ValueError("Builder function found but could not locate its position.")

    def strip_arg_value(self, value: str) -> str:
        lines = value.strip().splitlines()
        if len(lines) > 2:
            first, last = lines[0].strip(), lines[-1].strip()
            # Check if wrapped in multi-line {} or []
            if (first.endswith("{") and last.startswith("}")) or (
                first.endswith("[") and last.startswith("]")
            ):
                return "\n".join(lines[1:-1])
        return value

    def parse_args_to_dict(
        self, nix_lines: list[str]
    ) -> Union[dict[str, str], list[str], str]:
        """
        Parse lines of a Nix packaging expression. Returns only top-level keys and values.
        """
        res: dict[str, str] = {}
        current_key: str | None = None
        value_buffer: list[str] = []
        depth: int = 0

        for line in nix_lines:
            clean_line = line.strip()
            if not clean_line:
                continue

            # Check if a new top-level assignment is present
            if depth == 0 and "=" in clean_line:
                key, val = map(str.strip, clean_line.split("=", 1))
                current_key = key
                value_buffer = [val]
            elif current_key:
                value_buffer.append(clean_line)

            # Calculate new depth
            depth += sum(clean_line.count(b) for b in self.OPENING_CHARS)
            depth -= sum(clean_line.count(b) for b in self.CLOSING_CHARS)

            # Once depth returns to 0 and we have a ';' this means we have the full value
            if depth == 0 and current_key and clean_line.endswith(";"):
                res[current_key] = " \n ".join(value_buffer).rstrip(";")
                current_key = None
                value_buffer = []

        # Edge cases
        if not res:
            return nix_lines[0] if len(nix_lines) == 1 else nix_lines
        return res

    def clean_nix_value(self, val: Any) -> Any:
        if isinstance(val, dict):
            return {k: self.clean_nix_value(v) for k, v in val.items()}

        if isinstance(val, list):
            # Filter out artifact brackets and clean elements
            cleaned = [self.clean_nix_value(item) for item in val]
            return [i for i in cleaned if i not in ("", "[", "]", "{", "}")]

        if isinstance(val, str):
            val = val.strip()

            # 1. Handle Types
            val_lower = val.lower()
            type_map = {"true": True, "false": False, "null": None}
            if val_lower in type_map:
                return type_map[val_lower]

            # 2. Remove escaped and literal quotes safely
            if val.startswith('\\"') and val.endswith('\\"'):
                val = val[2:-2]
            elif val.startswith('"') and val.endswith('"'):
                val = val[1:-1]

            # 3. Handle stringified lists that didn't get parsed
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                return [self.clean_nix_value(x) for x in inner.split() if x]

        return val

    def parse(self) -> dict[str, Any]:
        builder_args_index = self.locate_builder_args()
        builder_args_lines = self.lines[builder_args_index:-1]

        args = self.parse_args_to_dict(builder_args_lines)

        if isinstance(args, dict):
            # Parse inner values using a dict comprehension for cleaner syntax
            content = {
                key: self.parse_args_to_dict(self.strip_arg_value(arg).splitlines())
                for key, arg in args.items()
            }
            return self.clean_nix_value(content)

        return self.clean_nix_value(args)


if __name__ == "__main__":
    parser = NixParser("nix-picking/example.nix")
    parsed_args = parser.parse()
    print(json.dumps(parsed_args, indent=2))
