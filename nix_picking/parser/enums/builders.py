from enum import Enum
import re


class Builders(str, Enum):
    PYTHON_PACKAGE = "buildPythonPackage"
    PYTHON_APP = "buildPythonApplication"
    GO_MODULE = "buildGoModule"
    RUST_PACKAGE = "buildRustPackage"

    @classmethod
    def get_builder_from_file(
        cls, file: str, pattern: str = r"\b\w*build\w*\b"
    ) -> "Builders | None":
        matches = re.findall(pattern, file)
        for match in matches:
            if match in cls._value2member_map_:
                return cls(match)
        return None


if __name__ == "__main__":
    with open("nix-picking/example.nix") as f:
        file_content = f.read()
    print(Builders.get_builder_from_file(file_content))
