from collections import defaultdict
from enum import Enum
import json


def reconstruct(lines):
    result = []
    for line in lines:
        if line.strip() == "":
            continue
        if line.strip().startswith("#"):
            continue
        result.append(line)
    return "\n".join(result)


class INDENTED_BLOCK_TYPE(Enum):
    LIST = "LIST"
    HASHMAP = "HASHMAP"


with open("nix-picking/example.nix") as f:
    lines = f.read().splitlines()

file = reconstruct(lines[13 : len(lines) - 2])
lines = file.splitlines()
res = defaultdict(str)
indented_block_name = None
indented_block_type = None

for line in lines:
    splited_line = line.split("=")
    key = None
    try:
        key, value = splited_line[0].strip(), splited_line[1].strip()
        print(f"Key: {key}")
        print(f"Value: {value}")
    except IndexError:
        value = splited_line[0].strip()
        print(f"{value}")

    if indented_block_name is not None:
        if not key:
            res[indented_block_name] += value + "\n "
        else:
            res[indented_block_name] += key + " = " + value + "\n "
    else:
        res[key] = value + "\n "

    if "[" in value and "]" in value:
        continue
    if value.endswith("{") or value.endswith("[") and indented_block_name is None:
        indented_block_name = key
        if value.endswith("{"):
            indented_block_type = INDENTED_BLOCK_TYPE.HASHMAP
        if value.endswith("["):
            indented_block_type = INDENTED_BLOCK_TYPE.LIST
    if (
        value.startswith("}") or value.startswith("]")
    ) and indented_block_name is not None:
        if indented_block_type == INDENTED_BLOCK_TYPE.HASHMAP and value.startswith("}"):
            indented_block_name = None
            indented_block_type = None
        if indented_block_type == INDENTED_BLOCK_TYPE.LIST and value.startswith("]"):
            indented_block_name = None
            indented_block_type = None

print(json.dumps(dict(res), indent=2))

#
# parsed = file.replace("=", ";").split(";")

# i = -1
# for value in parsed:
#     i += 1
#     if i % 2 == 0:
#         print(f"Key: {value.strip()}")
#         continue
#     print(f"Value: {value.strip()}")
