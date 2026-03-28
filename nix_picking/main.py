import re
import json

def clean_comments(text: str) -> str:
    """Removes Nix-style # comments safely."""
    # Removes full line comments and end-of-line comments
    # We use a simpler approach to avoid the 'nothing to repeat' error
    return re.sub(r"(?m)\s*#.*$", "", text)

def split_depth_aware(text: str, delimiter: str = ";") -> list:
    """Splits by delimiter at depth 0, handling multi-char delimiters like '++'."""
    statements = []
    current = ""
    depth = 0
    i = 0
    d_len = len(delimiter)
    
    while i < len(text):
        char = text[i]
        if char in "{[(": depth += 1
        elif char in "}])": depth -= 1
        
        # Look for delimiter only at top level
        if depth == 0 and text[i : i + d_len] == delimiter:
            if current.strip():
                statements.append(current.strip())
            current = ""
            i += d_len
            continue
        else:
            current += char
            i += 1
            
    if current.strip():
        statements.append(current.strip())
    return [s.strip() for s in statements]

def parse_nix_lazy(raw_value: str):
    if not isinstance(raw_value, str):
        return raw_value

    val = clean_comments(raw_value).strip()

    # --- STEP 0: Strip Lambda Header { lib, ... }: ---
    if val.startswith("{"):
        depth = 0
        for i in range(len(val)):
            if val[i] == "{": depth += 1
            elif val[i] == "}": depth -= 1
            if depth == 0 and val[i : i + 2] == "}:":
                val = val[i + 2 :].strip()
                break

    # --- STEP 1: Handle Concatenation (++) ---
    if "++" in val:
        parts = split_depth_aware(val, "++")
        if len(parts) > 1:
            return {"_type": "concatenation", "parts": parts}

    # --- STEP 2: Handle Derivation Wrapper ---
    wrapper_pattern = r"^([a-zA-Z0-9_-]+)\s+(?:rec\s+)?(?:\((.*?):\s*)?\{(.*)\}\s*\)?$"
    match = re.match(wrapper_pattern, val, re.DOTALL)
    if match:
        fname, fargs, fbody = match.groups()
        return {
            "_type": "derivation_wrapper",
            "function": fname,
            "fp_args": fargs.strip() if fargs else None,
            "content": parse_nix_lazy("{" + fbody + "}"),
        }

    # --- STEP 3: Handle Function Calls (lib.optionals ...) ---
    # Catch name followed by a space and then an argument starting with (, {, or [
    func_call_match = re.match(r"^([a-zA-Z0-9._-]+)\s+([\(\{\[])", val)
    if func_call_match:
        f_name = func_call_match.group(1)
        return {
            "_type": "function_call",
            "function": f_name,
            "raw_args": val[len(f_name):].strip(),
        }

    # --- STEP 4: Standard blocks ---
    if val.startswith("(") and val.endswith(")"):
        return parse_nix_lazy(val[1:-1].strip())

    if val.startswith("{") and val.endswith("}"):
        inner = val[1:-1].strip()
        res = {}
        for stmt in split_depth_aware(inner, ";"):
            if stmt.startswith("inherit "):
                res["_inherit"] = res.get("_inherit", []) + stmt.replace("inherit", "").split()
            elif "=" in stmt:
                k, v = stmt.split("=", 1)
                res[k.strip()] = v.strip()
        return res

    if val.startswith("[") and val.endswith("]"):
        # Split list items by space
        return [item for item in split_depth_aware(val[1:-1].strip(), " ") if item]

    return val

def parse_nix_full(input_data):
    if isinstance(input_data, str):
        node = parse_nix_lazy(input_data)
    else:
        node = input_data

    if isinstance(node, dict):
        n_type = node.get("_type")
        
        # Flatten concatenations into a single Python list
        if n_type == "concatenation":
            flattened = []
            for p in node["parts"]:
                parsed = parse_nix_full(p)
                if isinstance(parsed, list):
                    flattened.extend(parsed)
                else:
                    flattened.append(parsed)
            return flattened

        if n_type == "derivation_wrapper":
            return {"_type": "derivation", "function": node["function"], "args": parse_nix_full(node["content"])}

        if n_type == "function_call":
            # Split raw_args by space to catch multi-args like (condition) [list]
            args_list = split_depth_aware(node["raw_args"], " ")
            return {
                "_type": "function_call",
                "function": node["function"],
                "args": [parse_nix_full(a) for a in args_list]
            }

        # Recursive walk for attribute sets
        res = {}
        for k, v in node.items():
            if k in ["_type", "function", "fp_args"]: continue
            res[k] = v if k == "_inherit" else parse_nix_full(v)
        return res

    if isinstance(node, list):
        return [parse_nix_full(item) for item in node]

    # Clean quotes from strings
    if isinstance(node, str):
        node = node.strip()
        if node.startswith('"') and node.endswith('"'): return node[1:-1]
    return node

path = "tests/test_parser/assets/inputs/python/aetcd/default.nix"
with open(path, "r") as f:
    file = f.read()

data = parse_nix_full(file)

print(json.dumps(data, indent=2))
