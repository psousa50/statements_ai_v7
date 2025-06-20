#!/usr/bin/env python3
"""
Generate .env files from centralized YAML configuration.
This script reads config/settings.yaml and creates:
- .env (root, for Docker Compose)
- bank-statements-api/.env (backend)
- bank-statements-web/.env (frontend)

Usage:
  python scripts/generate_env_files.py
"""

import os
import sys
from pathlib import Path

import yaml

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_config():
    """Load the centralized configuration from YAML."""
    config_path = project_root / "config" / "settings.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def construct_urls_and_db(config):
    """Construct URLs and database connection string from ports and hosts."""
    ports = config["ports"]
    hosts = config["hosts"]
    db_config = config["database"]

    # Construct URLs
    api_base_url = f"http://{hosts['api']}:{ports['api']}"
    web_base_url = f"http://{hosts['web']}:{ports['web']}"

    # Construct database URL
    database_url = f"postgresql://{db_config['user']}:{db_config['password']}@{hosts['database']}:{ports['database']}/{db_config['name']}"

    return {
        "api_base_url": api_base_url,
        "web_base_url": web_base_url,
        "database_url": database_url,
        "api_url": api_base_url,  # For frontend
    }


def get_docker_ports(config):
    """Get Docker port mappings, using external ports as internal ports when they're the same."""
    ports = config["ports"]
    docker_config = config.get("docker", {})

    return {
        "api_internal": ports["api"],  # API uses same port internally and externally
        "web_internal": ports["web"],  # Web uses same port internally and externally
        "db_internal": docker_config.get(
            "db_internal_port", 5432
        ),  # DB uses different internal port
    }


def generate_root_env(config, urls):
    """Generate .env file for root (Docker Compose)."""
    env_content = f"""# Generated from config/settings.yaml - DO NOT EDIT MANUALLY
# Port configurations
API_PORT={config["ports"]["api"]}
WEB_PORT={config["ports"]["web"]}
DB_PORT={config["ports"]["database"]}

# URL configurations
API_BASE_URL={urls["api_base_url"]}
WEB_BASE_URL={urls["web_base_url"]}

# Database configuration
DATABASE_URL={urls["database_url"]}

# API Keys (add your actual keys here)
GOOGLE_API_KEY={config["secrets"]["google_api_key"]}
GEMINI_API_KEY={config["secrets"]["gemini_api_key"]}
"""

    root_env_path = project_root / ".env"
    with open(root_env_path, "w") as f:
        f.write(env_content)

    print(f"✅ Generated root .env file: {root_env_path}")


def generate_backend_env(config, urls):
    """Generate .env file for backend."""
    env_content = f"""# Generated from config/settings.yaml - DO NOT EDIT MANUALLY
# Port configurations
API_PORT={config["ports"]["api"]}
WEB_PORT={config["ports"]["web"]}
DB_PORT={config["ports"]["database"]}

# URL configurations
API_BASE_URL={urls["api_base_url"]}
WEB_BASE_URL={urls["web_base_url"]}

# Database configuration
DATABASE_URL={urls["database_url"]}

# API Keys (add your actual keys here)
GOOGLE_API_KEY={config["secrets"]["google_api_key"]}
GEMINI_API_KEY={config["secrets"]["gemini_api_key"]}
"""

    backend_env_path = project_root / "bank-statements-api" / ".env"
    with open(backend_env_path, "w") as f:
        f.write(env_content)

    print(f"✅ Generated backend .env file: {backend_env_path}")


def generate_frontend_env(config, urls):
    """Generate .env file for frontend."""
    env_content = f"""# Generated from config/settings.yaml - DO NOT EDIT MANUALLY
VITE_API_URL={urls["api_url"]}
WEB_PORT={config["ports"]["web"]}
"""

    frontend_env_path = project_root / "bank-statements-web" / ".env"
    with open(frontend_env_path, "w") as f:
        f.write(env_content)

    print(f"✅ Generated frontend .env file: {frontend_env_path}")


def main():
    """Main function to generate all .env files."""
    print("🔄 Generating .env files from centralized configuration...")

    try:
        config = load_config()
        urls = construct_urls_and_db(config)
        docker_ports = get_docker_ports(config)

        generate_root_env(config, urls)
        generate_backend_env(config, urls)
        generate_frontend_env(config, urls)

        print("\n🎉 All .env files generated successfully!")
        print("\n📝 To change configuration:")
        print("   1. Edit config/settings.yaml")
        print("   2. Run this script again: python scripts/generate_env_files.py")
        print("   3. Restart your services")

    except Exception as e:
        print(f"❌ Error generating .env files: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
