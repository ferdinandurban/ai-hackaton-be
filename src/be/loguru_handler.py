import logging
from loguru import logger

logger.add("debug.log", rotation="100 MB", level="DEBUG", format="{time} {level} {message}")


class LoguruHandler(logging.Handler):
    def emit(self, record):
        level = (
            logger.level(record.levelname).name
            if record.levelname in logger._core.levels
            else "INFO"
        )

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
