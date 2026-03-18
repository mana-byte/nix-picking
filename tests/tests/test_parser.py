import json
from os import listdir
from tests import INPUT_DIR, OUTPUT_DIR
from nix_picking.parser.nixparser import NixParser


def test_parser_against_previous_version():
    inputs_names = listdir(INPUT_DIR)
    for names in inputs_names:
        if names.endswith(".nix"):
            input_path = f"{INPUT_DIR}/{names}"
            output_path = f"{OUTPUT_DIR}/{names.replace('.nix', '.json')}"
            print(f"Testing parser for {input_path} against {output_path}")
            parser = NixParser(input_path)
            parsed_data = parser.parse()
            with open(output_path, "r") as f:
                expected_data = json.load(f)
            assert (
                parsed_data == expected_data
            ), f"Parsed data does not match expected data for {input_path}"
