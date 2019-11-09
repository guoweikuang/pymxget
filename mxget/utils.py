import re

regex = re.compile(r'[\\/:*?"<>|]')


def trim_invalid_file_path_chars(path: str) -> str:
    return regex.sub(' ', path)
