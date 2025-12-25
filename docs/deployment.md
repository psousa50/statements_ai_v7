# Deployment Guide

Deploy the Bank Statements app using free-forever services.

## Services Overview

| Component | Service | Cost |
|-----------|---------|------|
| Frontend | Cloudflare Pages | Free |
| Backend | Render | Free (750 hrs/month) |
| Database | Neon | Free (0.5GB) |
| AI | Google Gemini | Free tier |
| CI/CD | GitHub Actions | Free |

## Prerequisites

- GitHub account with repo pushed
- GitHub CLI installed (`brew install gh`) and logged in (`gh auth login`)

---

## Step 1: Get Neon Database URL

1. Go to [neon.tech](https://neon.tech) and sign in
2. Select your project (or create one)
3. Click on your branch (e.g., `production`)
4. In the **Connection Details** panel on the right:
   - Connection string dropdown → Select **Pooled connection**
   - Copy the connection string
5. **Important:** Change the driver prefix:
   - Neon shows: `postgresql://...`
   - Change to: `postgresql+psycopg://...` (add `+psycopg`)
   - Final format: `postgresql+psycopg://user:pass@host/dbname?sslmode=require`
6. Save this for `settings.prod.yaml` → `render_env.database_url`

### Finding the Connection String (Visual Guide)

```
Neon Dashboard
└── Your Project
    └── Branches → Click "production"
        └── Right panel: "Connection Details"
            └── Connection string (dropdown: "Pooled connection")
                └── Copy icon
```

---

## Step 2: Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click "Create API Key"
3. Copy the key
4. Save this for `settings.prod.yaml` → `render_env.gemini_api_key`

---

## Step 3: Set Up Cloudflare Pages

### 3.1 Create Cloudflare Account
1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) and sign up

### 3.2 Get Account ID
1. In dashboard, look at the URL: `dash.cloudflare.com/ACCOUNT_ID/...`
2. Or: Click any domain → Overview → right sidebar shows Account ID
3. Save this for `settings.prod.yaml` → `github.cloudflare_account_id`

### 3.3 Create API Token
1. Click profile icon (top right) → My Profile
2. Left sidebar → API Tokens
3. Click "Create Token"
4. Select "Create Custom Token" → Get started
5. Configure:
   - Name: `GitHub Actions Deploy`
   - Permissions: Account → Cloudflare Pages → Edit
6. Click Continue → Create Token
7. Copy the token (shown only once!)
8. Save this for `settings.prod.yaml` → `github.cloudflare_api_token`

### 3.4 Create Pages Project
1. Go to Workers & Pages → Create
2. Select "Pages" tab
3. Click "Upload assets" (Direct Upload)
4. Name: `statements-web`
5. Upload any placeholder file to create the project
6. Note your URL: `https://statements-web.pages.dev`

---

## Step 4: Set Up Render

### 4.1 Create Render Account
1. Go to [render.com](https://render.com) and sign up

### 4.2 Get API Key
1. Click profile icon → Account Settings
2. API Keys → Create new key
3. Copy the key
4. Save this for `settings.prod.yaml` → `render.api_key`

### 4.3 Connect Blueprint
1. Dashboard → New → Blueprint
2. Connect your GitHub repo
3. Render reads `render.yaml` and creates the service
4. Wait for initial deploy (will fail - that's OK, env vars not set yet)

### 4.4 Get Service ID
1. Click on the created service
2. Look at URL: `dashboard.render.com/web/srv-XXXXX`
3. Copy `srv-XXXXX`
4. Save this for `settings.prod.yaml` → `render.service_id`

### 4.5 Get Deploy Hook URL
1. In service → Settings
2. Scroll to "Build & Deploy"
3. Find "Deploy Hook" → Create Deploy Hook
4. Copy the URL
5. Save this for `settings.prod.yaml` → `github.render_deploy_hook_url`

---

## Step 5: Configure Google OAuth (if using)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. APIs & Services → Credentials
3. Edit your OAuth 2.0 Client ID
4. Add Authorized redirect URIs:
   - `https://statements-web.pages.dev/auth/callback`
5. Add Authorized JavaScript origins:
   - `https://statements-web.pages.dev`
6. Copy Client ID → `settings.prod.yaml` → `render_env.google_oauth_client_id`
7. Copy Client Secret → `settings.prod.yaml` → `render_env.google_oauth_client_secret`

---

## Step 6: Fill in settings.prod.yaml

Copy the example and fill in all values:

```bash
cp config/settings.prod.yaml.example config/settings.prod.yaml
```

```yaml
# config/settings.prod.yaml

render:
  api_key: "rnd_XXXXX"                    # From Step 4.2
  service_id: "srv-XXXXX"                 # From Step 4.4

github:
  cloudflare_account_id: "XXXXX"          # From Step 3.2
  cloudflare_api_token: "XXXXX"           # From Step 3.3
  render_deploy_hook_url: "https://..."   # From Step 4.5
  vite_api_url: "https://bank-statements-api.onrender.com"

render_env:
  database_url: "postgresql://..."        # From Step 1
  gemini_api_key: "XXXXX"                 # From Step 2
  jwt_secret_key: "XXXXX"                 # Generate below
  google_oauth_client_id: "XXXXX"         # From Step 5
  google_oauth_client_secret: "XXXXX"     # From Step 5
  web_base_url: "https://statements-web.pages.dev"
```

### Generate JWT Secret Key

```bash
openssl rand -hex 32
```

---

## Step 7: Push Secrets to Services

```bash
# Push GitHub secrets + Render env vars
pnpm deploy:setup
```

This runs:
- `setup-github-secrets.py` → pushes secrets to GitHub Actions + sets `DEPLOY_ENABLED=true`
- `setup-render-env.py` → pushes env vars to Render

---

## Step 8: Trigger First Deploy

Either:
- Push a commit to `main`
- Or manually re-run the workflow in GitHub Actions

---

## Step 9: Verify Deployment

1. **Backend**: Visit `https://bank-statements-api.onrender.com/docs`
2. **Frontend**: Visit `https://statements-web.pages.dev`

---

## Troubleshooting

### Render build fails
- Check logs in Render dashboard
- Ensure all env vars are set
- Verify `DATABASE_URL` format includes `?sslmode=require` for Neon

### Frontend shows API errors
- Check `VITE_API_URL` in GitHub secrets matches Render URL
- Check CORS: `WEB_BASE_URL` in Render env vars matches Cloudflare URL

### Cold starts on Render
- Free tier spins down after 15 mins of inactivity
- First request after idle takes 30-60 seconds
- This is expected behaviour for free tier

---

## File Reference

| File | Purpose |
|------|---------|
| `config/settings.prod.yaml` | Production secrets (gitignored) |
| `render.yaml` | Render service definition |
| `.github/workflows/deploy.yml` | CI/CD pipeline |
| `scripts/setup-github-secrets.py` | Push secrets to GitHub |
| `scripts/setup-render-env.py` | Push env vars to Render |

---

## Deplyment links
- Google Auth: https://console.cloud.google.com/apis/credentials?project=bank-statements-482016
- Render: https://dashboard.render.com/web/srv-d556v2dactks738d2fi0
- Cloudflare:  https://dash.cloudflare.com/e5bb20dbe9abd53e2ce8c90f8b8cda33/pages/view/bank-statements-web
- Neon: https://console.neon.tech/app/projects/plain-sound-47429716?database=neondb&branchId=br-misty-shape-a225ez7n
- Github: https://github.com/psousa50/statements_ai_v7
