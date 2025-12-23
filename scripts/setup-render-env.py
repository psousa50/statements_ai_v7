#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

import requests
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "settings.prod.yaml"

RENDER_ENV_VARS = [
    ("DATABASE_URL", ["render_env", "database_url"]),
    ("GEMINI_API_KEY", ["render_env", "gemini_api_key"]),
    ("JWT_SECRET_KEY", ["render_env", "jwt_secret_key"]),
    ("GOOGLE_OAUTH_CLIENT_ID", ["render_env", "google_oauth_client_id"]),
    ("GOOGLE_OAUTH_CLIENT_SECRET", ["render_env", "google_oauth_client_secret"]),
    ("WEB_BASE_URL", ["render_env", "web_base_url"]),
    ("API_BASE_URL", ["render_env", "api_base_url"]),
]


def load_config():
    if not CONFIG_FILE.exists():
        print(f"Error: {CONFIG_FILE} not found")
        print("Copy config/settings.prod.yaml.example to config/settings.prod.yaml and fill in values")
        sys.exit(1)

    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f)


def get_nested_value(config, keys):
    value = config
    for key in keys:
        value = value.get(key, "")
    return value or ""


def set_env_var(api_key, service_id, key, value):
    if not value:
        print(f"  Skipping {key} (empty)")
        return False

    url = f"https://api.render.com/v1/services/{service_id}/env-vars/{key}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.put(url, headers=headers, json={"value": value})

    if response.status_code in [200, 201]:
        print(f"  ✓ {key}")
        return True
    elif response.status_code == 404:
        response = requests.post(
            f"https://api.render.com/v1/services/{service_id}/env-vars",
            headers=headers,
            json={"key": key, "value": value}
        )
        if response.status_code in [200, 201]:
            print(f"  ✓ {key} (created)")
            return True

    print(f"  ✗ {key}: {response.status_code} - {response.text}")
    return False


def main():
    print("=== Render Environment Variables Setup ===\n")

    config = load_config()

    api_key = get_nested_value(config, ["render", "api_key"])
    service_id = get_nested_value(config, ["render", "service_id"])

    if not api_key:
        print("Error: render.api_key not set in settings.prod.yaml")
        print("Get your API key from: Render Dashboard → Account Settings → API Keys")
        sys.exit(1)

    if not service_id:
        print("Error: render.service_id not set in settings.prod.yaml")
        print("Find it in your service URL: https://dashboard.render.com/web/srv-XXXXX")
        sys.exit(1)

    print(f"Reading from: {CONFIG_FILE}")
    print(f"Service ID: {service_id}\n")
    print("Setting environment variables...")

    success_count = 0
    for env_name, config_path in RENDER_ENV_VARS:
        value = get_nested_value(config, config_path)
        if set_env_var(api_key, service_id, env_name, value):
            success_count += 1

    print(f"\nDone! {success_count}/{len(RENDER_ENV_VARS)} variables set")


if __name__ == "__main__":
    main()
