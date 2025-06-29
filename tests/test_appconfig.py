import tempfile
import json
from pathlib import Path
from src.configlib.configlib import AppConfig


def write_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def create_mock_config(temp_root: Path):
    config_dir = temp_root / "config"
    config_dir.mkdir()

    mock_data = {
        "log": {"level": "info"},
        "path": {"wiki": "Wiki"},
        "test": {"foo": "bar"}
    }
    write_json(config_dir / "config.json", mock_data)
    write_json(config_dir / "config_default.json", mock_data)
    return config_dir


import unittest

class TestAppConfig(unittest.TestCase):

    def test_appconfig_load_modify_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_dir = create_mock_config(tmp_path)

            # Load config
            config = AppConfig(project_root=tmp_path, rel_config_file_path="config")
            assert config.log["level"] == "info"
            assert config.path["wiki"] == (tmp_path / "Wiki").resolve()

            # Modify and save
            config.set("log", {"level": "debug"})
            config.save()

            # Reload and verify
            reloaded = AppConfig(project_root=tmp_path, rel_config_file_path="config")
            assert reloaded.log["level"] == "debug"

            # Reset and verify
            reloaded.reset_to_default()
            assert reloaded.log["level"] == "info"

            # Backup should exist
            backup_path = config.config_file.with_suffix(".json.bak")
            assert backup_path.exists()

        # All checks passed
