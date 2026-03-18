import json
from typing import Any
from pathlib import Path
from .enums.builders import Builders


class NixParser:
    """
    A simple parser for simple nix expressions and simple minds.
    """

    OPENING_CHARS: set[str] = {"{", "[", "("}
    CLOSING_CHARS: set[str] = {"}", "]", ")"}

    def __init__(self):
        pass

    def __to_lines(self, nix_expression_or_lines: list[str] | str) -> list[str]:
        if isinstance(nix_expression_or_lines, list):
            lines = nix_expression_or_lines
        else:
            lines = nix_expression_or_lines.splitlines()
        return lines


    def locate_builder_args(self, nix_expression_or_lines: list[str] | str) -> int:
        lines = self.__to_lines(nix_expression_or_lines)

        builder = Builders.get_builder_from_file("\n".join(lines))

        if not builder:
            raise ValueError("No builder function found in the file.")

        for i in range(len(lines) - 1, -1, -1):
            if builder.value in lines[i]:
                return i + 1

        raise ValueError("Builder function found but could not locate its position.")

    def strip_arg_value(self, value: str) -> str:
        lines = value.strip().splitlines()
        if len(lines) < 2:
            return value
        first, last = lines[0].strip(), lines[-1].strip()
        is_set = first.endswith("{") and last.startswith("}")
        is_list = first.endswith("[") and last.startswith("]")
        is_str_block = first.endswith("''") and last.startswith("''")
        if is_set or is_list or is_str_block:
            header_content = first[:-1].strip()
            if header_content:
                inner_body = "\n".join(lines[1:-1])
                if is_set:
                    return f"function = {header_content};\n{inner_body}"
                if is_list:
                    return f"function = {header_content};\nlist_content = [\n{inner_body}\n];"
            return "\n".join(lines[1:-1])
        return value

    def parse_args_to_dict(
        self, nix_expression_or_lines: str | list[str]
    ) -> dict[str, str] | list[str] | str:
        """
        Parse lines of a Nix packaging expression. Returns only top-level keys and values.
        """
        res: dict[str, str] = {}
        current_key: str | None = None
        value_buffer: list[str] = []
        depth: int = 0
        nix_lines = self.__to_lines(nix_expression_or_lines)

        for line in nix_lines:
            clean_line = line.strip()
            if not clean_line:
                continue
            if clean_line.startswith("#"):
                continue

            if depth == 0 and " = " in clean_line:
                key, val = map(str.strip, clean_line.split("=", 1))
                current_key = key
                value_buffer = [val]
            elif current_key:
                value_buffer.append(clean_line)

            depth += sum(clean_line.count(b) for b in self.OPENING_CHARS)
            depth -= sum(clean_line.count(b) for b in self.CLOSING_CHARS)

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
            cleaned = [self.clean_nix_value(item) for item in val]
            return [i for i in cleaned if i not in ("", "[", "]", "{", "}")]

        if isinstance(val, str):
            val = val.strip()
            val_lower = val.lower()
            type_map = {"true": True, "false": False, "null": None}
            if val_lower in type_map:
                return type_map[val_lower]
            if val.startswith('\\"') and val.endswith('\\"'):
                val = val[2:-2]
            elif val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                return [self.clean_nix_value(x) for x in inner.split() if x]

        return val

    def parse(self, nix_expression_or_lines: list[str] | str) -> dict[str, Any]:
        """
        Parse the first two levels of the nix expression into a dictionary.
        This is meant to be used for the nix packaging expressions of nixpkgs. See NixOS/nixpkgs for more info.
        """
        lines = self.__to_lines(nix_expression_or_lines)

        builder_args_index = self.locate_builder_args(lines)
        builder_args_lines = lines[builder_args_index:-1]
        args = self.parse_args_to_dict(builder_args_lines)

        if isinstance(args, dict):
            content = {
                key: self.parse_args_to_dict(self.strip_arg_value(arg).splitlines())
                for key, arg in args.items()
            }
            return self.clean_nix_value(content)

        return self.clean_nix_value(args)


if __name__ == "__main__":
    parser = NixParser()
    parsed_args = parser.parse("buildPythonPackage { \n Nothing \n }")
    print(json.dumps(parsed_args, indent=2))
