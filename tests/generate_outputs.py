"""
This script generates JSON output files for tests.
This is to see if the output is consistent through different versions of the package.
THIS IS NOT TO CHECK IF THE OUTPUT IS CORRECT
"""

import os
from tests.utils import list_files_recursive


if __name__ == "__main__":
    import json
    from tests import INPUT_DIR, OUTPUT_DIR
    from nix_picking.parser.nixparser import NixParser

    inputs_names = list_files_recursive(INPUT_DIR)

    for names in inputs_names:
        if names.endswith(".nix"):
            input_path = f"{names}"
            output_path = f"{names.replace('.nix', '.json').replace(INPUT_DIR, OUTPUT_DIR)}"
            print(f"Generating output for {input_path} -> {output_path}")

            parser = NixParser()
            with open(input_path, "r") as f:
                parsed_data = parser.parse(f.read())

            output_path_dir = os.path.dirname(output_path)
            if not os.path.exists(output_path_dir):
                os.makedirs(output_path_dir)

            with open(output_path, "w") as f:
                json.dump(parsed_data, f, indent=2)
