import json
from typing import LiteralString


def reconstruct(lines):
    result = []
    for line in lines:
        if line.strip() == "":
            continue
        if line.strip().startswith("#"):
            continue
        result.append(line)
    return "\n".join(result)


def parse_nix_to_dict(nix_lines: list[LiteralString] | list[str]) -> dict[str, str]:
    """
    Parse lines of a Nix packaging expression. What gets returned is only the top-level keys and values.
    To get nested values, you can call this function recursively on the value of a key.
    This is a naïve parser but should work for simple expressions.
    """
    res: dict[str, str] = {}
    current_key = None
    value_buffer = []
    depth = 0

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


with open("nix-picking/example.nix") as f:
    lines = f.read().splitlines()

file = reconstruct(lines[35 : len(lines) - 1])
res = parse_nix_to_dict(file.splitlines())
meta = res["meta"]
res_ = parse_nix_to_dict(meta.splitlines()[1:-1])
print(json.dumps(res, indent=2))
print(json.dumps(res_, indent=2))
