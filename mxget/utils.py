import re


def trim_invalid_file_path_chars(path: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', ' ', path)

