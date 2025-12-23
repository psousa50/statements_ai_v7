#!/usr/bin/env python3
import sys
from pathlib import Path

import yaml

project_root = Path(__file__).parent.parent


def load_config():
    config_path = project_root / "config" / "settings.local.yaml"
    if not config_path.exists():
        print(f"Error: {config_path} not found")
        print("Copy config/settings.local.yaml.example to config/settings.local.yaml")
        sys.exit(1)
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def generate_root_env(config):
    ports = config["local"]["ports"]
    content = f"""API_PORT={ports["api"]}
WEB_PORT={ports["web"]}
DB_PORT={ports["database"]}

API_BASE_URL={config["urls"]["api"]}
WEB_BASE_URL={config["urls"]["web"]}

DATABASE_URL={config["database"]["url"]}

GEMINI_API_KEY={config["secrets"].get("gemini_api_key", "")}
"""
    path = project_root / ".env"
    with open(path, "w") as f:
        f.write(content)
    print(f"  {path}")


def generate_backend_env(config):
    ports = config["local"]["ports"]
    secrets = config["secrets"]
    content = f"""API_PORT={ports["api"]}
WEB_PORT={ports["web"]}
DB_PORT={ports["database"]}

API_BASE_URL={config["urls"]["api"]}
WEB_BASE_URL={config["urls"]["web"]}

DATABASE_URL={config["database"]["url"]}

GEMINI_API_KEY={secrets.get("gemini_api_key", "")}
JWT_SECRET_KEY={secrets.get("jwt_secret_key", "")}
GOOGLE_OAUTH_CLIENT_ID={secrets.get("google_oauth_client_id", "")}
GOOGLE_OAUTH_CLIENT_SECRET={secrets.get("google_oauth_client_secret", "")}
"""
    path = project_root / "bank-statements-api" / ".env"
    with open(path, "w") as f:
        f.write(content)
    print(f"  {path}")


def generate_frontend_env(config):
    ports = config["local"]["ports"]
    content = f"""VITE_API_URL={config["urls"]["api"]}
WEB_PORT={ports["web"]}
"""
    path = project_root / "bank-statements-web" / ".env"
    with open(path, "w") as f:
        f.write(content)
    print(f"  {path}")


def main():
    print("Generating .env files from config/settings.local.yaml\n")
    config = load_config()
    generate_root_env(config)
    generate_backend_env(config)
    generate_frontend_env(config)
    print("\nDone")


if __name__ == "__main__":
    main()
