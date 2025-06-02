from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.app import register_app_routes
from app.core.config import settings
from app.core.dependencies import provide_dependencies
from app.logging.config import init_logging

init_logging()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_app_routes(app, provide_dependencies)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )
