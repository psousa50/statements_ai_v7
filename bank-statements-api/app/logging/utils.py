import logging


def log_exception(message, *args, logger_name="app", **kwargs):
    logger = logging.getLogger(logger_name)
    kwargs.setdefault("exc_info", True)
    logger.error(message, *args, **kwargs)
