import tempfile
import json
from pathlib import Path
from configlib.appconfig import AppConfig


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

    def test_values_set_as_attributes_are_saved(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / "config"
            config_dir.mkdir()
            data = {"paths": {}, "build": {"lang": "de"}, "stats": {"last_build": ""}}
            write_json(config_dir / "config.json", data)
            write_json(config_dir / "config_default.json", data)

            config = AppConfig(config_dir / "config.json")
            config.stats.last_build = "2026-10-22T20:01:00"
            config.stats.successful_files = {"de": ["a.pdf"]}
            config.build.manuals_all = ["TEST"]
            config.save()

            saved = json.loads((config_dir / "config.json").read_text(encoding="utf-8"))
            assert saved["stats"] == {"last_build": "2026-10-22T20:01:00", "successful_files": {"de": ["a.pdf"]}}
            assert saved["build"] == {"lang": "de", "manuals_all": ["TEST"]}
            assert AppConfig(config_dir / "config.json").stats.last_build == "2026-10-22T20:01:00"

    def test_section_keys_can_be_listed_and_deleted(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / "config"
            config_dir.mkdir()
            data = {"paths": {}, "manuals": {"TEST": 0, "Händler": 1}}
            write_json(config_dir / "config.json", data)
            write_json(config_dir / "config_default.json", data)

            config = AppConfig(config_dir / "config.json")
            assert list(config.manuals) == ["TEST", "Händler"]
            del config.manuals.TEST
            setattr(config.manuals, "GatewayTool", 0)
            config.save()

            saved = json.loads((config_dir / "config.json").read_text(encoding="utf-8"))
            assert saved["manuals"] == {"Händler": 1, "GatewayTool": 0}
            with self.assertRaises(AttributeError):
                del config.manuals.TEST

    def test_appconfig_load_modify_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_dir = tmp_path / "config"
            config_dir.mkdir()

            # Use the actual JSON structure from the project
            with open(Path(__file__).parent.parent / "config" / "config.json", "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Write the actual config data to our test files
            write_json(config_dir / "config.json", config_data)
            write_json(config_dir / "config_default.json", config_data)

            # Load config
            config = AppConfig(config_dir / "config.json")

            # Test initial values
            original_log_level = config._config_data["log"]["lvl"]
            assert original_log_level == "info"

            # Modify config
            config._config_data["log"]["lvl"] = "debug"
            config.save()

            # Reload and verify changes
            reloaded = AppConfig(config_dir / "config.json")
            assert reloaded._config_data["log"]["lvl"] == "debug"

            # Reset to default by copying default content
            default_content = json.loads((config_dir / "config_default.json").read_text(encoding="utf-8"))
            reloaded._config_data = default_content
            reloaded.save()

            # Verify reset worked
            reset_config = AppConfig(config_dir / "config.json")
            assert reset_config._config_data["log"]["lvl"] == original_log_level

            # Check backup was created
            backup_path = config.config_file.with_suffix(".json.bak")
            assert backup_path.exists()

        # All checks passed
