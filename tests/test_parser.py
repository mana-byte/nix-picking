import json
from typing import Any
from nix_picking.parser.nixparser import NixParser

def test_parser_1():
    parser = NixParser("tests/nix/example.nix")
    parsed_args = parser.parse()
    with open("tests/expected/example.json", "r") as f:
        expected: dict[str, Any] = json.load(f)
    assert parsed_args == expected
