import logging
import os

class LoggerEngine:

    def __init__(self, log_file="data/system.log"):

        os.makedirs("data", exist_ok=True)

        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s"
        )

    def info(self,msg):
        logging.info(msg)
        print(msg)

    def error(self,msg):
        logging.error(msg)
        print(msg)

    def warn(self,msg):
        logging.warning(msg)
        print(msg)
