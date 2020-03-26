#!/usr/bin/python3

import signal
import logging


class ApplicationKiller:
    is_running = True

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)

    def exit(self, signum, frame):
        logger = logging.getLogger("killer")
        logger.warning("stopping application")
        self.is_running = False
