from pathlib import Path
from typing import Dict


class PathResolver:
    def __init__(self, paths: Dict[str, str], base: Path):
        self._paths = paths
        self._base = base

    def __getitem__(self, key):
        if key not in self._paths:
            raise KeyError(f"Path key '{key}' not found.")
        return (Path(self._base) / Path(self._paths[key])).resolve()

    def __setitem__(self, key, value):
        self._paths[key] = value

    def __delitem__(self, key):
        del self._paths[key]

    def as_dict(self):
        return self._paths
