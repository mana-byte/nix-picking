from typing import Any, LiteralString
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
        indexes = [i for i, line in enumerate(self.lines) if builder.value in line]
        if not indexes:
            raise ValueError(
                "Builder function found but could not locate its position in the file."
            )
        return max(indexes) + 1

    def strip_arg_value(self, value: str) -> str:
        lines = value.splitlines()
        is_there_indent_marker = (
            "{" in lines[0] and "}" in lines[-1] or "[" in lines[0] and "]" in lines[-1]
        ) and len(lines) > 2
        try:
            if is_there_indent_marker:
                remove_indent_marker = value.split("\n")[1:-1]
                return "\n".join(remove_indent_marker)
            else:
                raise IndexError
        except IndexError:
            return value

    def parse_args_to_dict(
        self, nix_lines: list[LiteralString] | list[str]
    ) -> dict[str, str] | list[str] | list[LiteralString] | str:
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

        # edge cases
        if res == {}:
            if len(nix_lines) == 1:
                return nix_lines[0]
            return nix_lines
        return res

    def clean_nix_value(self, val) -> Any:
        if isinstance(val, dict):
            return {k: self.clean_nix_value(v) for k, v in val.items()}

        if isinstance(val, list):
            # Filter out artifact brackets like "[" or "]" and clean elements
            cleaned_list = [self.clean_nix_value(item) for item in val]
            return [i for i in cleaned_list if i not in ("", "[", "]", " {", " }")]

        if isinstance(val, str):
            val = val.strip()

            # 1. Handle Booleans
            if val.lower() == "true":
                return True
            if val.lower() == "false":
                return False
            if val.lower() == "null":
                return None

            # 2. Remove escaped and literal quotes
            # This handles both \"pygithub\" and "pygithub"
            if (val.startswith('"') and val.endswith('"')) or (
                val.startswith('\\"') and val.endswith('\\"')
            ):
                val = val.strip('\\"')

            # 3. Handle stringified lists/sets that didn't get parsed
            # e.g., '[ "github" ]' -> ["github"]
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                return [self.clean_nix_value(x) for x in inner.split() if x]

            return val

        return val

    def parse(self) -> dict[str, Any]:
        content = {}
        builder_args_index = self.locate_builder_args()
        builder_args_lines = self.lines[builder_args_index:-1]
        args = self.parse_args_to_dict(builder_args_lines)
        if isinstance(args, dict):
            for key, arg in args.items():
                arg = self.strip_arg_value(arg)
                content[key] = self.parse_args_to_dict(arg.splitlines())
        return self.clean_nix_value(content)


if __name__ == "__main__":
    import json

    parser = NixParser("nix-picking/example.nix")
    parsed_args = parser.parse()
    print(json.dumps(parsed_args, indent=2))
