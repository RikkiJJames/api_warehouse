import pandas as pd
from pathlib import Path

class FileLoader:
    """
    A class to load data from files.
    """

    def __init__(self, folder_path : str | Path):
        self.folder_path = Path(folder_path)

    def get_files(self, suffix: str) -> list[Path]:
        """
        Reads a file and returns the content as a string.
        """

        suffix = suffix if suffix.startswith(".") else f".{suffix}"
        search_dir = self.folder_path
        if not search_dir.is_absolute():
            search_dir = self.folder_path

        return sorted(search_dir.rglob(f"*{suffix}"))

    def read_file(self, file_path: Path) -> str:
        """
        Reads a file and returns the content as a string.
        """
        with open(file_path, "r") as f:
            content = f.read()

        return content


