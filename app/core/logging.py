import sys

from loguru import logger


def setup_logging() -> None:
    # Remove default handler
    logger.remove()

    # Add a professional format for terminal
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level="INFO",
    )

    # In a real production environment, we'd add a JSON file handler here
    logger.add("logs/app.log", rotation="10 MB", retention="10 days", level="DEBUG")


setup_logging()
