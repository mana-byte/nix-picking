"""
This script generates JSON output files for tests.
This is to see if the output is consistent through different versions of the package.
THIS IS NOT TO CHECK IF THE OUTPUT IS CORRECT
"""

if __name__ == "__main__":
    import json
    from os import listdir
    from tests import INPUT_DIR, OUTPUT_DIR
    from nix_picking.parser.nixparser import NixParser

    inputs_names = listdir(INPUT_DIR)

    for names in inputs_names:
        if names.endswith(".nix"):
            input_path = f"{INPUT_DIR}/{names}"
            output_path = f"{OUTPUT_DIR}/{names.replace('.nix', '.json')}"
            print(f"Generating output for {input_path} -> {output_path}")

            parser = NixParser(input_path)
            parsed_data = parser.parse()

            with open(output_path, "w") as f:
                json.dump(parsed_data, f, indent=2)
