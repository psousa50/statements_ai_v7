# Centralized Application Configuration (YAML-based)

This directory contains the **single source of truth** for all ports, URLs, and other application settings used across the entire project.

## How It Works

- **Edit**: `config/settings.yaml` (your personal config file)
- **Generate**: Run `python scripts/generate_env_files.py` to create all needed `.env` files
- **Use**: Each service (backend, frontend, Docker Compose) loads its own `.env` file

## Files

- `settings.yaml.example` — Template configuration file (committed to git)
- `settings.yaml` — Your personal configuration (gitignored)
- `../scripts/generate_env_files.py` — Script to generate all `.env` files
- `.env` (root, generated) — Used by Docker Compose
- `../bank-statements-api/.env` (generated) — Used by backend
- `../bank-statements-web/.env` (generated) — Used by frontend

## Quick Start

1. **Copy the example config**

   ```bash
   cp config/settings.yaml.example config/settings.yaml
   ```

2. **Customize your settings**
   - Edit `config/settings.yaml` to change ports, URLs, etc.
   - Add your API keys in the `secrets` section

3. **Generate .env files**

   ```bash
   python scripts/generate_env_files.py
   ```

4. **Start your services**

   ```bash
   ./scripts/start_services.sh
   ```

## Why this approach?

- **Single source of truth**: No duplication, no risk of drift
- **Security**: Only the right variables go to the right service
- **Automation**: No manual copying or editing of `.env` files
- **Personalization**: Each developer can use their own ports/URLs
- **Team consistency**: Everyone starts with the same template

## Example Workflow

```bash
# 1. Copy and customize config
cp config/settings.yaml.example config/settings.yaml
# Edit config/settings.yaml to change ports or add API keys

# 2. Generate .env files
python scripts/generate_env_files.py

# 3. Start your services
./scripts/start_services.sh
```

## Notes

- Do **not** edit the generated `.env` files directly. Always edit `settings.yaml` and regenerate.
- The `settings.yaml` file is gitignored so you can customize it without affecting others.
- You can add/remove variables in `settings.yaml` as your project grows.
- For production, you can use the generated `.env` files or set environment variables directly in your deployment environment.

---

**Old config files (`app_config.py`, `app_config.js`, `setup_env.sh`) are no longer used and have been removed.** 