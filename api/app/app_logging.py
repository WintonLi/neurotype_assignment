import logging
from logging import handlers
from pathlib import Path

# ANSI color codes for terminal output
COLOR_CODES = {
    "DEBUG": "\033[94m",     # Blue
    "INFO": "\033[92m",      # Green
    "WARNING": "\033[93m",   # Yellow
    "ERROR": "\033[91m",     # Red
    "CRITICAL": "\033[91m",  # Red
}

RESET_CODE = "\033[0m"


class ColoredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        color = COLOR_CODES.get(levelname)

        if color:
            record_copy = logging.makeLogRecord(record.__dict__.copy())
            record_copy.levelname = f"{color}{levelname}{RESET_CODE}"
            return super().format(record_copy)

        return super().format(record)


def configure_logging(
    log_file: str | Path | None = None,
    max_bytes: int = 1024 * 1024,
    backup_count: int = 3,
) -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    console_formatter = ColoredFormatter(
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )

    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file is not None:
        log_path = Path(log_file).expanduser().resolve()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# Directory containing this Python file.
_MODULE_DIR = Path(__file__).resolve().parent

# Adjust the number of parents according to your project structure.
_LOG_FILE = _MODULE_DIR.parent / "logs" / "ui_backend.log"

logger = configure_logging(log_file=_LOG_FILE)
