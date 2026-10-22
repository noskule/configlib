from pathlib import Path
import json
from typing import Any, Dict, Iterator, Union, List


class ConfigSection:
    """
    Attribute view of one config dict. Reads and writes go to the dict
    itself, so AppConfig.save() writes values set as attributes.
    """
    def __init__(self, data: Dict[str, Any]) -> None:
        object.__setattr__(self, "_data", data)

    def __getattr__(self, name: str) -> Any:
        try:
            value = self._data[name]
        except KeyError:
            raise AttributeError(f"No config key '{name}'.") from None
        return ConfigSection(value) if isinstance(value, dict) else value

    def __setattr__(self, name: str, value: Any) -> None:
        self._data[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self._data[name]
        except KeyError:
            raise AttributeError(f"No config key '{name}'.") from None

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)


class PathGroup:
    """
    Represents a named group of paths under one root directory.
    Provides attribute access to each entry and the root directory.
    """
    def __init__(self, spec: Dict[str, Any]) -> None:
        self._root = Path(spec["root_dir"]).resolve()
        self._entries: Dict[str, str] = spec.get("entries", {})

    @property
    def root_dir(self) -> Path:
        """Absolute root directory for this group."""
        return self._root

    def __getattr__(self, name: str) -> Path:
        if name in self._entries:
            return (self._root / self._entries[name]).resolve()
        raise AttributeError(f"No path entry '{name}' in this group.")

    def list_entries(self) -> List[str]:
        """Return all entry keys in this group."""
        return list(self._entries.keys())

    def has_entry(self, name: str) -> bool:
        """Check if an entry exists in this group."""
        return name in self._entries

    def add_entry(self, name: str, rel_path: str) -> None:
        """Add a new relative path entry to this group."""
        if name in self._entries:
            raise KeyError(f"Entry '{name}' already exists.")
        self._entries[name] = rel_path

    def remove_entry(self, name: str) -> None:
        """Remove an existing path entry from this group."""
        if name not in self._entries:
            raise KeyError(f"Entry '{name}' does not exist.")
        del self._entries[name]


class MultiRootPathResolver:
    """
    Allows namespaced path resolution via attribute access:
    cfg.paths.<group>.<entry>
    """
    def __init__(self, spec: Dict[str, Dict[str, Any]]) -> None:
        self._spec = spec

    def __getattr__(self, group: str) -> PathGroup:
        if group in self._spec:
            return PathGroup(self._spec[group])
        raise AttributeError(f"No path group '{group}'.")

    def list_groups(self) -> List[str]:
        """Return all defined path groups."""
        return list(self._spec.keys())

    def has_group(self, group: str) -> bool:
        """Check if a path group exists."""
        return group in self._spec


class AppConfig:
    """
    Application configuration manager.

    Args:
        config_file_path: Path to the project's config.json file.

    Attributes:
        paths: MultiRootPathResolver for namespaced path access.
        Other top-level config sections exposed as namespaces.
    """
    REQUIRED_KEYS = ["paths"]

    def __init__(self, config_file_path: Union[str, Path]) -> None:
        self.config_file = Path(config_file_path)
        self.config_default = self.config_file.with_name(
            f"{self.config_file.stem}_default{self.config_file.suffix}"
        )
        self._config_data: Dict[str, Any] = {}

        self._ensure_file()
        self._load()
        self.validate()

        # Attribute access to all non-path sections
        for key, val in self._config_data.items():
            if key != "paths":
                setattr(self, key, ConfigSection(val) if isinstance(val, dict) else val)

        # Namespaced path resolver
        self.paths = MultiRootPathResolver(self._config_data["paths"])

    def _ensure_file(self) -> None:
        if not self.config_file.is_file():
            if self.config_default.is_file():
                text = self.config_default.read_text(encoding="utf-8")
                self.config_file.write_text(text, encoding="utf-8")
            else:
                # Create minimal default structure if none exists
                default_template: Dict[str, Any] = {"paths": {}}
                self.config_default.write_text(
                    json.dumps(default_template, indent=4, ensure_ascii=False),
                    encoding="utf-8"
                )
                self.config_file.write_text(
                    json.dumps(default_template, indent=4, ensure_ascii=False),
                    encoding="utf-8"
                )

    def _load(self) -> None:
        try:
            self._config_data = json.loads(
                self.config_file.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError:
            default = json.loads(
                self.config_default.read_text(encoding="utf-8")
            )
            self.config_file.write_text(
                json.dumps(default, indent=4, ensure_ascii=False),
                encoding="utf-8"
            )
            self._config_data = default

    def validate(self) -> None:
        for key in self.REQUIRED_KEYS:
            if key not in self._config_data:
                raise KeyError(f"Missing required section '{key}' in config.json")

    def save(self) -> None:
        # Backup existing config
        if self.config_file.is_file():
            backup = self.config_file.with_suffix('.json.bak')
            self.config_file.replace(backup)
        # Write updated config data
        text = json.dumps(self._config_data, indent=4, ensure_ascii=False)
        self.config_file.write_text(text, encoding="utf-8")


if __name__ == '__main__':
    # Example usage with reference config.json
    import os

    def p_title(s: str) -> str:
        print("\n# ", s.upper() if s else '')


    config = AppConfig('../config/config.json')
    p_title("Config Loading")
    print(f"Config loaded from: {config.config_file}")

    p_title("Access build settings")
    print(f"cfg.build['mode']: {config.build.mode}")
    print(f"cfg.git['branch']: {config.git.branch}")
    print(f"cfg.paths.data.toc_matrix: {config.paths.data.toc_matrix}")
    print(f"cfg.paths.project.config: {config.paths.project.config}")

    p_title("Add entry")
    config.paths.data.remove_entry('test')
    config.paths.data.add_entry('test', 'path/to/test')
    print("cfg.paths.data.add_entry('test', 'path/to/test')")
    print(f"cfg.paths.data.test: {config.paths.data.test}")

    p_title("Delete entry")
    print(f"config.paths.data.remove_entry('test): {config.paths.data.remove_entry('test')}")

    p_title("List available path groups")
    print(f"cfg.paths.list_groups(): {config.paths.list_groups()}")

    p_title("Inspect project group")
    proj = config.paths.project
    print("proj = cfg.paths.project")
    print(f"proj.root_dir: {proj.root_dir}")
    print(f"proj.config: {proj.config}")

    p_title("Inspect data group")
    data = config.paths.data
    print("data = cfg.paths.data")
    print(f"data.root_dir: {data.root_dir}")
    for entry in data.list_entries():
        print(f"  * data.{entry}: {getattr(data, entry)}")

    p_title("Check non-existent group")
    print(f"cfg.paths.has_group('archive'): {config.paths.has_group('archive')}")

    p_title("Dynamically add new path group")
    self_spec = {
        'root_dir': os.getcwd(),
        'entries': {'temp': 'temp'}
    }
    config._config_data['paths']['self'] = self_spec
    print(f"cfg.paths.self.temp: {config.paths.self.temp}")
    # config.save()
    p_title("Config Save")
    print("Config updated and saved.")
