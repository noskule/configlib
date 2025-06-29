from pathlib import Path
import json
import ast
from typing import Any, Dict, Union
from configlib.pathresolver import PathResolver


class AppConfig:
    """
    Application configuration manager that supports runtime updates,
    auto-conversion of values, and safe JSON persistence.

    Parameters:
        project_root (str | Path | None): The root directory of the project. If None, defaults to module location.
        rel_config_file_path (str): Path (relative to project_root) where config.json and config_default.json are located.

    Attributes:
        config_file: The active configuration file.
        config_file_default: The fallback default configuration.
        path: A dynamic path dictionary with all relative paths resolved to absolute.

    Example:
        config = AppConfig(project_root="/my/project", rel_config_file_path="config")
        print(config.log["level"])
    """
    REQUIRED_KEYS = ["log", "path"]

    def __init__(self, project_root: Union[str, Path], rel_config_file_path: str) -> None:
        self.project_root: Path = Path(project_root).resolve()
        self.config_dir: Path = (self.project_root / rel_config_file_path).resolve()
        self.config_file = self.config_dir / 'config.json'
        self.config_file_default = self.config_dir / 'config_default.json'
        self._config_data: Dict[str, Any] = {}

        self._ensure_file()
        self._load()
        self.validate()
        self.path = PathResolver(self._config_data.get("path", {}), self.project_root)

    def _ensure_file(self) -> None:
        """
        Ensure that the main config file exists.

        - If `config.json` is missing, copy `config_default.json` to replace it.
        - Raises a FileNotFoundError if neither file exists.
        """
        if not self.config_file.is_file():
            if self.config_file_default.is_file():
                default_text = self.config_file_default.read_text(encoding='utf-8')
                self.config_file.write_text(default_text, encoding='utf-8')
            else:
                raise FileNotFoundError(
                    f"Config missing and default not found: \n    {self.config_file}\n    {self.config_file_default}")

    def _process_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively process a nested dictionary and convert leaf string values.

        - Attempts to cast strings into Python primitives (int, float, list, bool).
        - Returns a dictionary with typed values.

        Args:
            config (dict): Raw config dictionary loaded from JSON.

        Returns:
            dict: The processed, typed configuration dictionary.
        """
        def try_cast(value: Any) -> Any:
            if not isinstance(value, str):
                return value
            value = value.strip()
            try:
                return ast.literal_eval(value)
            except (ValueError, SyntaxError):
                return value

        return {
            key: self._process_config(val) if isinstance(val, dict) else try_cast(val)
            for key, val in config.items()
        }

    def _load_json_file(self, path: Path) -> Dict[str, Any]:
        """
        Load a JSON file from the given path.

        Args:
            path (Path): Path to a JSON file.

        Returns:
            dict: Parsed JSON content.

        Raises:
            ValueError: If the file contains invalid JSON.
        """
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON at {path}: {e}")

    def _load(self) -> None:
        """
        Load the configuration from disk.

        - Tries loading `config.json`; if invalid, falls back to `config_default.json`.
        - Casts values using `_process_config()`.
        - Sets all top-level keys as attributes on the AppConfig instance.
        """
        try:
            raw = self._load_json_file(self.config_file)
        except ValueError:
            raw = self._load_json_file(self.config_file_default)
            self.config_file.write_text(json.dumps(raw, indent=4, ensure_ascii=False), encoding='utf-8')

        self._config_data = self._process_config(raw)
        for key, val in self._config_data.items():
            setattr(self, key, val)

    def save(self) -> None:
        """
        Save the current configuration to disk.

        - Creates a backup of the existing config file as `config.json.bak`.
        - Serializes internal data with indentation and UTF-8 encoding.
        - Does not validate against schema; assumes prior validation.
        """
        if self.config_file.is_file():
            backup_path = self.config_file.with_suffix('.json.bak')
            self.config_file.replace(backup_path)

        serialized = json.dumps(self._config_data, indent=4, ensure_ascii=False)
        self.config_file.write_text(serialized, encoding='utf-8')

    def reset_to_default(self) -> None:
        """
        Overwrite the current config with the default version.

        - Replaces `config.json` with `config_default.json`.
        - Reloads and reinitializes config state.
        """
        if not self.config_file_default.is_file():
            raise FileNotFoundError(f"Default config missing: {self.config_file_default}")
        self.config_file.write_text(self.config_file_default.read_text(encoding='utf-8'), encoding='utf-8')
        self._load()

    def validate(self) -> None:
        """
        Validate that all required top-level keys exist.

        Raises:
            KeyError: if any required key is missing.
        """
        for key in self.REQUIRED_KEYS:
            if key not in self._config_data:
                raise KeyError(f"Missing required config section: '{key}'")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a config entry by key.

        Args:
            key (str): The top-level key to fetch.
            default (Any): Fallback value if key is missing.

        Returns:
            Any: The value of the config entry.
        """
        return self._config_data.get(key, default)

    def has(self, key: str) -> bool:
        """
        Check if a key exists in the configuration.

        Args:
            key (str): The top-level key to check.

        Returns:
            bool: True if present, False otherwise.
        """
        return key in self._config_data

    def set(self, key: str, value: Any, strict: bool = True) -> None:
        """
        Update or add a config entry.

        Args:
            key (str): The top-level key to modify or add.
            value (Any): The value to assign to the key.
            strict (bool): If True, only existing keys may be modified.

        Raises:
            KeyError: If key doesn't exist and strict is True.
            TypeError: If merging incompatible types.
        """
        if strict and key not in self._config_data:
            raise KeyError(f"Unknown config key: {key}")

        # Ensure that dicts are only merged with dicts
        if key in self._config_data and isinstance(self._config_data[key], dict):
            if not isinstance(value, dict):
                raise TypeError(f"Expected dict for key '{key}', got {type(value).__name__}")

        if isinstance(self._config_data[key], dict) and isinstance(value, dict):
            self._config_data[key] = {**self._config_data[key], **value}
        else:
            self._config_data[key] = value
        setattr(self, key, self._config_data[key])


if __name__ == '__main__':
    project_root = Path(__file__).parent.resolve()
    print("[INFO] Project Root:", project_root)
    config = AppConfig(project_root, '../config')

    print("[INFO] Wiki Path:", config.path['wiki'])
    print("[INFO] Project Root:", config.project_root)

    print("[UPDATE] Setting 'log.level' to 'debug'")
    config.set('log', {"level": "debug"})

    print("[UPDATE] Setting 'test.foo' to 'baz'")
    config.set('test', {"foo": "baz"})

    print("[ADD] Adding new path 'backup': 'Backups'")
    config.path['backup'] = 'Backups'
    print("[INFO] New path added:", config.path['backup'])

    print("[MODIFY] Updating 'backup' path to absolute archive location")
    config.path['backup'] = 'Archives'
    print("[INFO] Modified path:", config.path['backup'])

    print("[DELETE] Removing 'backup' path from config")
    del config.path['backup']
    print("[INFO] Path 'backup' removed.")

    # Persist the changes
    config.save()
    print("[INFO] Configuration saved.")

    # Show updated test key
    print("[DEBUG] Test section:", config.test)

    # Reset to default
    print("[RESET] Reverting to default configuration...")
    config.reset_to_default()
    print("[INFO] Configuration reset.")
