import logging
import os
import uuid
from datetime import datetime, timedelta


class DynamicContentFileHandler(logging.Handler):
    def __init__(self, directory="logs/files"):
        super().__init__()
        self.directory = directory
        self.max_age_days = 7

    def emit(self, record):
        try:
            os.makedirs(self.directory, exist_ok=True)

            self.delete_old_files()

            prefix = getattr(record, "prefix", "log")
            ext = getattr(record, "ext", "log")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S.%f")
            uid = uuid.uuid4().hex[:8]
            filename = f"{timestamp}_{prefix}_{uid}.{ext}"
            filepath = os.path.join(self.directory, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.format(record))
        except Exception:
            self.handleError(record)

    def delete_old_files(self):
        now = datetime.now()
        cutoff = now - timedelta(days=self.max_age_days)

        for filename in os.listdir(self.directory):
            filepath = os.path.join(self.directory, filename)
            if os.path.isfile(filepath):
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime < cutoff:
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
