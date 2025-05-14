import logging.config
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "../..", "logs")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "raw": {"format": "%(message)s"},
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "big_file": {
            "class": "app.logging.dynamic_file_handler.DynamicContentFileHandler",
            "level": "DEBUG",
            "formatter": "raw",
            "directory": os.path.join(LOG_DIR, "files"),
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "app.log"),
            "formatter": "standard",
        },
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
        },
    },
    "loggers": {
        "app.llm.big": {"handlers": ["big_file"], "level": "DEBUG", "propagate": False},
        "app": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": True},
    },
}


def init_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)
