import sys
from pathlib import Path

from loguru import logger as _logger

_LOG_DIR = Path(__file__).parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

_logger.remove()
_logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | {message}",
    level="INFO",
    colorize=True,
)
_logger.add(
    _LOG_DIR / "bot_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <7} | {message}",
    level="DEBUG",
    rotation="00:00",
    retention=10,
    encoding="utf-8",
)

log = _logger
