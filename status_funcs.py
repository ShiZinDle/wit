import filecmp
import os
from typing import Iterator

import utilities


def get_all_files(path: str) -> Iterator[str]:
    """Yield absolute path to all files in `path` directory tree."""
    for folder in os.walk(path):
        directory, sub_directories, files = folder
        if '.wit' in path or '.wit' not in directory:
            for sub_directory in sub_directories:
                sub_directory_fullname = os.path.join(directory, sub_directory)
                if not os.listdir(sub_directory_fullname):
                    yield sub_directory_fullname
            for file in files:
                yield os.path.join(directory, file)


def get_changed_files(og_path: str, new_path: str) -> Iterator[str]:
    """Yield all files in `og_path` with different content from the corresponding files in `new_path`."""
    og_path_files, new_path_files = [list(get_all_files(path)) for path in (og_path, new_path)]
    for og_file in og_path_files:
        for new_file in new_path_files:
            if utilities.get_original_name(og_file) == utilities.get_original_name(new_file):
                if not filecmp.cmp(og_file, new_file) and not os.path.isdir(og_file):
                    yield utilities.get_original_name(og_file)


def get_nonexistent_files(og_path: str, new_path: str) -> Iterator[str]:
    """Yield all files in `og_path` not present in `new_path`."""
    og_path_files, new_path_files = [list(get_all_files(path)) for path in (og_path, new_path)]
    for og_file in og_path_files:
        if utilities.get_original_name(og_file) not in (utilities.get_original_name(file) for file in new_path_files):
            yield utilities.get_original_name(og_file)