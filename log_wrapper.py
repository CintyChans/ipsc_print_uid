import logging
import os
from datetime import datetime


class NoNewlineFileHandler(logging.FileHandler):
    def emit(self, record=True):
        try:
            msg = self.format(record)
            with open(self.baseFilename, self.mode, encoding="utf-8") as file:
                file.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)

    def close(self):
        super().close()


def init(uid, role, firmware, log_level=logging.INFO):
    file_dir = "logs"
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    formatter = logging.Formatter("%(message)s")
    file_name = f"{file_dir}/{datetime.now().strftime('%Y%m%d_%H%M%S')}-{uid}-{role}-{firmware}.log"
    file_handler = NoNewlineFileHandler(file_name)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(file_handler)
    logger.setLevel(log_level)

    logging.info(f"logger init, file_name={file_name}")
    return file_name, logger, file_handler
