import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict

class Logger:
    """
    Structured JSONL logger.
    Each image gets its own log file under logs/YYYY-MM-DD/.
    """

    def __init__(self, image_id: str, base_dir: Path = Path("logs"), verbose: bool = False) -> None:
        self.image_id = image_id
        self.verbose = verbose

        date_str = dt.datetime.now().strftime("%Y-%m-%d")
        self.log_dir = base_dir / date_str
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_path = self.log_dir / f"{image_id}.jsonl"

    def _write(self, level: str, message: str, **kwargs: Any) -> None:
        entry = {
            "time": dt.datetime.now().isoformat(),
            "level": level,
            "image_id": self.image_id,
            "message": message,
            **kwargs,
        }

        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        if self.verbose:
            print(f"[{level.upper()}] {message}", file=sys.stderr)

    def info(self, message: str, **kwargs: Any) -> None:
        self._write("info", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._write("error", message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        self._write("debug", message, **kwargs)
