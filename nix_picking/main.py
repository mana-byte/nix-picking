import re
import json

import re


def split_depth_aware(text: str, delimiter: str = ";") -> list:
    """Splits by delimiter at depth 0, ignoring semicolons in 'with' headers."""
    statements = []
    current = ""
    depth = 0
    in_with_header = False
    i = 0
    while i < len(text):
        char = text[i]
        if char in "{[(":
            depth += 1
        elif char in "}])":
            depth -= 1

        if depth == 0 and text[i : i + 5] == "with ":
            in_with_header = True

        if char == delimiter and depth == 0:
            if in_with_header and delimiter == ";":
                in_with_header = False
                current += char
            else:
                if current.strip():
                    statements.append(current.strip())
                current = ""
        else:
            current += char
        i += 1
    if current.strip():
        statements.append(current.strip())
    return statements


def parse_nix_lazy(raw_value: str):
    """
    Universal Lazy Parser.
    Now handles the leading dependency block '{ ... }:' automatically.
    """
    val = raw_value.strip()

    # --- STEP 0: Strip the leading Dependency Lambda { ... }: ---
    # If the string starts with '{' and has a '}:' before 'buildPythonPackage'
    if val.startswith("{"):
        # Find the first '}:' at depth 0
        depth = 0
        for i in range(len(val)):
            if val[i] == "{":
                depth += 1
            elif val[i] == "}":
                depth -= 1
            if depth == 0 and val[i : i + 2] == "}:":
                # Strip everything up to and including the ': '
                val = val[i + 2 :].strip()
                break

    # --- STEP 1: Handle Derivation Wrapper: function (args: { ... }) ---
    func_wrapper_match = re.match(
        r"^([a-zA-Z0-9_-]+)\s*\((.*?):\s*\{(.*)\}\)$", val, re.DOTALL
    )
    if func_wrapper_match:
        fname, fargs, fbody = func_wrapper_match.groups()
        return {
            "_type": "derivation_wrapper",
            "function": fname,
            "fp_args": fargs.strip(),
            "content": parse_nix_lazy("{" + fbody + "}"),
        }

    # --- STEP 2: Handle 'with' scoping ---
    if val.startswith("with "):
        header_end = val.find(";")
        return {
            "_type": "with_scope",
            "scope": val[5:header_end].strip(),
            "body": val[header_end + 1 :].strip(),
        }

    # --- STEP 3: Handle Function Calls (fetchFromGitHub { ... }) ---
    func_call_match = re.match(r"^([a-zA-Z0-9._-]+)\s+([\(\{\[])", val)
    if func_call_match:
        return {
            "_type": "function_call",
            "function": func_call_match.group(1),
            "raw_args": val[len(func_call_match.group(1)) :].strip(),
        }

    # --- STEP 4: Handle Attribute Sets ---
    if val.startswith("{") and val.endswith("}"):
        inner = val[1:-1].strip()
        res = {}
        for stmt in split_depth_aware(inner, ";"):
            if "=" in stmt:
                k, v = stmt.split("=", 1)
                res[k.strip()] = v.strip()
        return res

    # --- STEP 5: Handle Lists ---
    if val.startswith("[") and val.endswith("]"):
        return split_depth_aware(val[1:-1].strip(), " ")

    return val


def parse_nix_full(input_data):
    """
    Recursively parses a Nix string or walks an already parsed lazy dict.
    """
    # 1. If it's a string, we need to "unfold" it into a lazy node first
    if isinstance(input_data, str):
        node = parse_nix_lazy(input_data)
    else:
        node = input_data

    # 2. If it's a derivation wrapper, parse its 'content'
    if isinstance(node, dict) and node.get("_type") == "derivation_wrapper":
        return {
            "_type": "derivation",
            "function": node["function"],
            "fp_args": node.get("fp_args"),
            "args": parse_nix_full(node["content"]),
        }

    # 3. If it's a function call, parse its raw_args
    if isinstance(node, dict) and node.get("_type") == "function_call":
        return {
            "_type": "function_call",
            "function": node["function"],
            "args": parse_nix_full(node["raw_args"]),
        }

    # 4. If it's a 'with' scope, parse the body string
    if isinstance(node, dict) and node.get("_type") == "with_scope":
        return {
            "_type": "with_scope",
            "scope": node["scope"],
            "body": parse_nix_full(node["body"]),
        }

    # 5. If it's a dictionary (Attribute Set), recurse through keys
    if isinstance(node, dict):
        return {
            k: parse_nix_full(v)
            for k, v in node.items()
            if k not in ["_type", "function", "fp_args"]
        }

    # 6. If it's a list, recurse through items
    if isinstance(node, list):
        return [parse_nix_full(item) for item in node]

    # 7. Base case: raw values
    return node


path = "tests/test_parser/assets/inputs/python/a2a-sdk/default.nix"
with open(path, "r") as f:
    file = f.read()

data = parse_nix_full(file)

print(json.dumps(data, indent=2))
