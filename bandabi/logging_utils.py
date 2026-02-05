# bandabi/logging_utils.py
import logging
from pathlib import Path

def setup_logger(name: str, log_file: Path, level=logging.INFO):
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "[%(asctime)s][%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # console
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)

    # file
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger
