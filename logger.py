import logging
import os
from datetime import datetime

os.makedirs("logs", exist_ok=True)

def setup_logger():
    logger = logging.getLogger("AutoRedeem")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(
        "logs/auto_%s.log" % datetime.now().strftime('%Y%m%d'),
        encoding='utf-8'
    )
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    fmt = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

logger = setup_logger()
