import logging

logging.basicConfig(format="[%(asctime)s] %(name)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %I:%M:%S",
                    level=logging.INFO)


class Log:
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
