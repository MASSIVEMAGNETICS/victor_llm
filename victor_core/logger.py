import os
import datetime
import traceback

class VictorLoggerStub:
    def __init__(self, component="DefaultComponent"):
        self.component = component
        self.log_level_str = os.environ.get("VICTOR_LOG_LEVEL", "INFO").upper()
        self.log_levels_map = {"DEBUG": 1, "INFO": 2, "WARN": 3, "ERROR": 4, "CRITICAL": 5}
        self.current_log_level_int = self.log_levels_map.get(self.log_level_str, 2)

    def _log(self, level, message, **kwargs):
        level_int = self.log_levels_map.get(level.upper(), 2)
        if self.current_log_level_int <= level_int:
            log_entry = (f"[{datetime.datetime.utcnow().isoformat(sep='T', timespec='milliseconds')}Z]"
                         f"[{level.ljust(8)}] [{self.component.ljust(25)}] {message}")
            if kwargs.get("exc_info", False):
                import traceback
                log_entry += f"\n{traceback.format_exc()}"
            print(log_entry)

    def info(self, message, **kwargs): self._log("INFO", message, **kwargs)
    def debug(self, message, **kwargs): self._log("DEBUG", message, **kwargs)
    def warn(self, message, **kwargs): self._log("WARN", message, **kwargs)
    def error(self, message, **kwargs): self._log("ERROR", message, **kwargs)
    def critical(self, message, **kwargs): self._log("CRITICAL", message, **kwargs)
