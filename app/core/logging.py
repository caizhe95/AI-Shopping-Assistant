import logging

from app.core.config import settings

def setup_logging():
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    )
    return logging.getLogger(settings.app_name)

logger = setup_logging()
