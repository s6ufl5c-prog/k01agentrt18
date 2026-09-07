import os
import yaml
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "redeemer": {
        "headless": False,
        "user_data_dir": "./google_profile",
        "timeout": 30,
        "auto_confirm": True,
        "proxy": "",
        "clipboard_poll_interval": 1.0,
    },
    "notifications": {
        "enabled": False,
        "type": "webhook",
        "telegram": {
            "bot_token": "",
            "chat_id": "",
        },
        "webhook_url": "",
    }
}

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file or return defaults."""
    if not os.path.exists(config_path):
        example_path = "config.example.yaml"
        if os.path.exists(example_path):
            try:
                with open(example_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or DEFAULT_CONFIG
            except Exception:
                return DEFAULT_CONFIG
        return DEFAULT_CONFIG

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
            if isinstance(loaded, dict):
                # Merge with defaults
                merged = DEFAULT_CONFIG.copy()
                for k, v in loaded.items():
                    if isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
                        merged[k].update(v)
                    else:
                        merged[k] = v
                return merged
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"Warning: Failed to parse {config_path}: {e}. Using defaults.")
        return DEFAULT_CONFIG
