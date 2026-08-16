"""config — load config.yaml and compute a content hash for results logging."""

import hashlib
from pathlib import Path

import yaml


_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.yaml"


class Config:
    """Immutable configuration loaded from config.yaml.

    Usage
    -----
    cfg = Config.load()
    print(cfg.horizon_days, cfg.beta_window, cfg.seed)
    """

    def __init__(self, raw: dict):
        self._raw = raw
        self._hash = None

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        path = Path(path) if path else _CONFIG_PATH
        with open(path) as f:
            raw = yaml.safe_load(f)
        return cls(raw)

    @property
    def config_hash(self) -> str:
        """Deterministic SHA-256 of the config file contents (12-char hex)."""
        if self._hash is None:
            with open(_CONFIG_PATH, "rb") as f:
                self._hash = hashlib.sha256(f.read()).hexdigest()[:12]
        return self._hash

    # -- convenience accessors so code can do cfg.horizon_days etc. ---------
    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._raw:
            return self._raw[name]
        raise AttributeError(f"Unknown config key: {name}")

    def __repr__(self) -> str:
        return f"Config(keys={list(self._raw.keys())}, hash={self.config_hash})"
