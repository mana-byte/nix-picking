from enum import Enum
import re



class Builders(str, Enum):
    PYTHON_PACKAGE = "buildPythonPackage"
    PYTHON_APP = "buildPythonApplication"
    GO_MODULE = "buildGoModule"
    RUST_PACKAGE = "buildRustPackage"
    STANDARD = "stdenv.mkDerivation"
    STANDARD_CC = "stdenvNoCC.mkDerivation"

    @classmethod
    def get_builder_from_file(
        cls, file: str, pattern: str = ""
    ) -> "Builders | None":
        if not pattern:
            for builder, builder_pattern in PATTERNS.items():
                if re.search(builder_pattern, file):
                    return builder
        matches = re.findall(pattern, file)
        for match in matches:
            if match in cls._value2member_map_:
                return cls(match)
        return None


if __name__ == "__main__":
    with open("nix-picking/example.nix") as f:
        file_content = f.read()
    print(Builders.get_builder_from_file(file_content))


PATTERNS = {
    Builders.PYTHON_PACKAGE: r"\b\w*buildPythonPackage\w*\b",
    Builders.PYTHON_APP: r"\b\w*buildPythonApplication\w*\b",
    Builders.GO_MODULE: r"\b\w*buildGoModule\w*\b",
    Builders.RUST_PACKAGE: r"\b\w*buildRustPackage\w*\b",
    Builders.STANDARD: r"\bstdenv\.mkDerivation\b",
    Builders.STANDARD_CC: r"\bstdenvNoCC\.mkDerivation\b",
}
