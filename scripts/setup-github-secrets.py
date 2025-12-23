#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "settings.prod.yaml"

GITHUB_SECRETS = [
    ("CLOUDFLARE_ACCOUNT_ID", ["deployment", "github", "cloudflare_account_id"]),
    ("CLOUDFLARE_API_TOKEN", ["deployment", "github", "cloudflare_api_token"]),
    ("RENDER_DEPLOY_HOOK_URL", ["deployment", "github", "render_deploy_hook_url"]),
    ("VITE_API_URL", ["urls", "api"]),
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


def check_gh_cli():
    try:
        subprocess.run(["gh", "auth", "status"], capture_output=True, check=True)
    except FileNotFoundError:
        print("Error: GitHub CLI (gh) not installed")
        print("Install with: brew install gh")
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("Error: Not logged in to GitHub CLI")
        print("Run: gh auth login")
        sys.exit(1)


def set_secret(name, value):
    if not value:
        print(f"  Skipping {name} (empty)")
        return False

    result = subprocess.run(
        ["gh", "secret", "set", name],
        input=value.encode(),
        capture_output=True
    )

    if result.returncode == 0:
        print(f"  {name}")
        return True
    else:
        print(f"  {name}: {result.stderr.decode()}")
        return False


def set_variable(name, value):
    result = subprocess.run(
        ["gh", "variable", "set", name],
        input=value.encode(),
        capture_output=True
    )

    if result.returncode == 0:
        print(f"  {name}")
        return True
    else:
        print(f"  {name}: {result.stderr.decode()}")
        return False


def main():
    print("GitHub Secrets Setup\n")

    check_gh_cli()
    config = load_config()

    print(f"Reading from: {CONFIG_FILE}\n")
    print("Setting secrets...")

    success_count = 0
    for secret_name, config_path in GITHUB_SECRETS:
        value = get_nested_value(config, config_path)
        if set_secret(secret_name, value):
            success_count += 1

    print(f"\nDone! {success_count}/{len(GITHUB_SECRETS)} secrets set")

    print("\nSetting variables...")
    set_variable("DEPLOY_ENABLED", "true")

    print("\nVerify with: gh secret list && gh variable list")


if __name__ == "__main__":
    main()
