import os


def list_files_recursive(path=".") -> list[str]:
    res: list[str] = []
    for entry in os.listdir(path):
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            res = res + list_files_recursive(full_path)
        else:
            res.append(full_path)
    return res
