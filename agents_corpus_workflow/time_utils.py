from __future__ import annotations

from datetime import datetime


def timestamp_now() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d%H%M%S")


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
