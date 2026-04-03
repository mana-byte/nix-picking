import tree_sitter_nix
from tree_sitter import Language, Parser, Query, QueryCursor


def nix_to_python(node, source_code: bytes):
    """Recursively converts a Tree-sitter Nix node into a Python object."""
    node_type = node.type

    if node_type == "string_expression":
        text = source_code[node.start_byte : node.end_byte].decode("utf-8")
        if text.startswith('""') and text.endswith('""'):
            return ""
        if text.startswith('"'):
            return text[1:-1]
        if text.startswith("''"):
            return text[2:-2].strip()
        return text

    elif node_type == "list_expression":
        return [
            nix_to_python(c, source_code)
            for c in node.children
            if c.type not in ["(", ")", "[", "]", "{", "}", ";", ","]
        ]

    elif node_type in ["attrset_expression", "rec_attrset_expression"]:
        result = {}
        for child in node.children:
            if child.type == "binding":
                attrpath = child.child_by_field_name("attrpath")
                expression = child.child_by_field_name("expression")
                if attrpath and expression:
                    key = source_code[attrpath.start_byte : attrpath.end_byte].decode(
                        "utf-8"
                    )
                    result[key] = nix_to_python(expression, source_code)
        return result

    elif node_type == "boolean_expression":
        return source_code[node.start_byte : node.end_byte].decode("utf-8") == "true"

    elif node_type == "integer_expression":
        return int(source_code[node.start_byte : node.end_byte].decode("utf-8"))

    elif node_type == "apply_expression":
        func_node = node.children[0]
        return source_code[func_node.start_byte : func_node.end_byte].decode("utf-8")

    return source_code[node.start_byte : node.end_byte].decode("utf-8")


def get_nix_attribute_value(file_path: str, attribute_path: str, raw: bool = False):
    """
    Finds a Nix attribute and returns either a Python object or the raw string.
    """
    lang_data = tree_sitter_nix.language()
    NIX_LANGUAGE = Language(lang_data)
    parser = Parser(NIX_LANGUAGE)

    with open(file_path, "rb") as f:
        source_code = f.read()

    tree = parser.parse(source_code)
    parts = attribute_path.split(".")
    current_node = tree.root_node

    for part in parts:
        query_str = f"""
            (binding 
                attrpath: (attrpath (identifier) @name (#eq? @name "{part}"))
                expression: (_) @value)
        """
        query = Query(NIX_LANGUAGE, query_str)
        cursor = QueryCursor(query)
        captures = cursor.captures(current_node)

        value_nodes = captures.get("value", [])
        if not value_nodes:
            return None

        current_node = value_nodes[0]

    if raw:
        return current_node.text
    return nix_to_python(current_node, source_code)


path = "tests/test_parser/assets/inputs/python/a2a-sdk/default.nix"

value = get_nix_attribute_value(path, "disabledTests", raw=True)

print(value)
