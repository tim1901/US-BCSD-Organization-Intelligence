import logging
from app.core.logging import configure_logging
logger=logging.getLogger(__name__)
def run():
    configure_logging(); logger.info('Scheduler maintenance pass started')
if __name__=='__main__': run()
