# AppConfig

**AppConfig** is a flexible, developer-friendly JSON configuration manager for Python applications.  
It supports runtime updates, automatic type casting, fallback defaults, and absolute path resolution using relative path storage.


## 🔧 Features

- 📂 Loads config from a primary JSON file with auto-fallback to a default backup
- 🔁 Supports dynamic config changes with optional strict key enforcement
- 🧠 Auto-casts strings into Python types (`int`, `float`, `list`, `bool`)
- 🗂 Resolves relative file paths to absolute paths using `PathResolver`
- 💾 Automatically creates a backup (`.json.bak`) on save
- 🧪 Easy to test, LLM- and IDE-friendly with full docstring coverage



## 🚀 Installation

Clone this repository and install locally:

```bash
git clone https://github.com/yourusername/appconfig.git
cd appconfig
pip install -e .
```
Or include it directly in your src/ layout and import via:

```python
from configlib.src import AppConfig
```

# ⚡ Quickstart

```python
from configlib.src import AppConfig
from pathlib import Path

project_root = Path(__file__).parent
config = AppConfig(project_root, 'config')

print(config.log['level'])  # Access a config value
print(config.path['wiki'])  # Auto-resolved absolute path
```

# Modify and save
```python
config.set('log', {'level': 'debug'})
config.save()
```

# 📁 Config File Layout

Your config/ folder should include:

* **config.json:** main user-facing config
* **config_default.json:** fallback used if config.json is missing or corrupted

Example:

    {
      "log": { "level": "info" },
      "path": { "wiki": "WikiPages" },
      "test": { "foo": "bar" }
    }


# 🧪 Testing

Run all tests using pytest

Test file: tests/test_appconfig.py
Includes config loading, modification, backup validation, and reset-to-default behavior.


# 📌 Project Structure

    src/
    ├── configlib/
    │   ├── appconfig.py
    │   ├── pathresolver.py
    │   └── config/
    │       ├── config.json
    │       └── config_default.json
    tests/
    └── test_appconfig.py


# 📚 API Overview
Method	Description
AppConfig()	Load and prepare configuration
.get(key)	Retrieve value or None
.set(key, val)	Update value (with strict type merge)
.save()	Persist changes, with .bak backup
.reset_to_default()	Overwrite with the default config
.path['key']	Get resolved absolute path



# 📚 License

MIT License. See LICENSE file for details.


# 🙌 Contributing

Pull requests are welcome. Please ensure all tests pass and style guides are followed before submitting.