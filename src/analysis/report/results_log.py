"""results_log — append-only JSONL log of every analysis run.

Each record contains
    - timestamp (ISO-8601)
    - config_hash (12-char SHA-256 of config.yaml)
    - git_commit (HEAD SHA)
    - phase (str label, e.g. "B0", "B1", "exploratory")
    - key_outputs (dict of summary statistics / paths)
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from ..config import Config

_LOG_PATH = Path(__file__).resolve().parent.parent.parent.parent / "results_log.jsonl"


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=_LOG_PATH.parent,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


class ResultsLog:
    """Append-only JSONL results log.

    Usage
    -----
    log = ResultsLog()
    log.append(phase="B0", key_outputs={"r2_mean": 0.034, "n_stocks": 277})
    """

    def __init__(self, log_path: Path | None = None):
        self.path = log_path or _LOG_PATH

    def append(self, phase: str, key_outputs: dict, cfg: Config | None = None) -> None:
        """Append one record to the results log."""
        if cfg is None:
            cfg = Config.load()
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config_hash": cfg.config_hash,
            "git_commit": _git_head(),
            "phase": phase,
            "key_outputs": key_outputs,
        }
        with open(self.path, "a") as f:
            f.write(json.dumps(record) + "\n")

    def load(self) -> list[dict]:
        """Read all log records into a list."""
        if not self.path.exists():
            return []
        with open(self.path) as f:
            return [json.loads(line) for line in f if line.strip()]
