"""Portable storage interfaces. Research parameters belong to the analysis code."""
import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def _settings():
    configured = os.environ.get("RESEARCH_CONFIG")
    path = Path(configured).expanduser() if configured else PROJECT_ROOT / "config.local.json"
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if not path.exists():
        if configured:
            raise FileNotFoundError(f"Explicit local configuration does not exist: {path}")
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Local configuration must be a JSON object")
    return data


def project_path(role, relative=""):
    """Resolve storage roles using environment variables or private local JSON.

    Only output directories are created. Input files are never manufactured and
    no file is overwritten here. Prepared previous-stage results consumed by
    legacy analysis functions belong under OUTPUT_ROOT as described in docs.
    """
    names = {"data": "DATA_ROOT", "outputs": "OUTPUT_ROOT", "labels": "LABELS_ROOT"}
    defaults = {"data": "data", "outputs": "outputs", "labels": "labels"}
    if role not in names:
        raise ValueError(f"Unknown storage role: {role}")
    local = _settings()
    root = Path(os.environ.get(names[role], local.get(names[role], defaults[role]))).expanduser()
    if not root.is_absolute():
        root = PROJECT_ROOT / root
    tail = Path(str(relative).replace("\\", "/"))
    if tail.is_absolute() or ".." in tail.parts:
        raise ValueError("Storage interface requires a relative path inside its configured root")
    path = root / tail
    if role == "outputs":
        file_suffixes = {".csv", ".txt", ".log", ".png", ".pdf", ".svg", ".gexf", ".xlsx", ".json"}
        directory = path.parent if path.suffix.lower() in file_suffixes else path
        directory.mkdir(parents=True, exist_ok=True)
    return str(path)
