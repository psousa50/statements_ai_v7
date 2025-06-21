import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

# Load environment variables from the backend .env file
backend_env_path = Path(__file__).parent / ".env"
load_dotenv(backend_env_path)


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8000"))
    print(f"Starting API server on port {port}")
    uvicorn.run("app.main:app", host="::", port=port, reload=True, reload_dirs=["app"])
