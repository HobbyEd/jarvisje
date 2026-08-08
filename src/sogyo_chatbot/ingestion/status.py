"""Shared ingest status on the data volume (ADR-010).

API and worker processes share these files under settings.data_dir.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import settings

STATUS_NAME = "ingest_status.json"
STOP_NAME = "ingest_stop.flag"
LOCK_NAME = "ingest.lock"

DEFAULT_STATUS: dict[str, Any] = {
    "status": "idle",
    "progress": 0,
    "message": "Geen indexering actief",
    "started_at": None,
    "finished_at": None,
    "current_source": None,
    "error": None,
    "stop_requested": False,
    "pages_scraped": 0,
    "chunks_indexed": 0,
    "pid": None,
    "run_id": None,
}


def _data_dir() -> Path:
    d = Path(settings.data_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def status_path() -> Path:
    return _data_dir() / STATUS_NAME


def stop_path() -> Path:
    return _data_dir() / STOP_NAME


def lock_path() -> Path:
    return _data_dir() / LOCK_NAME


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_status() -> dict[str, Any]:
    """Read status JSON; reconcile dead PIDs."""
    path = status_path()
    if not path.is_file():
        return dict(DEFAULT_STATUS)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return dict(DEFAULT_STATUS)
    except Exception:
        return dict(DEFAULT_STATUS)

    st = {**DEFAULT_STATUS, **data}
    # If marked running but process is gone, surface as error/stale
    if st.get("status") == "running":
        pid = st.get("pid")
        if pid and not _pid_alive(int(pid)):
            st["status"] = "error"
            st["message"] = (
                st.get("message") or "Indexering"
            ) + " (worker-proces niet meer actief)"
            st["error"] = st.get("error") or "worker_pid_dead"
            st["finished_at"] = st.get("finished_at") or utc_now_iso()
            st["stop_requested"] = False
            try:
                write_status(st)
            except Exception:
                pass
            _clear_lock_if_stale()
    return st


def write_status(update: dict[str, Any], merge: bool = True) -> dict[str, Any]:
    """Atomically write status (merge with existing by default)."""
    path = status_path()
    if merge and path.is_file():
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(current, dict):
                current = dict(DEFAULT_STATUS)
        except Exception:
            current = dict(DEFAULT_STATUS)
        current.update(update)
        data = current
    else:
        data = {**DEFAULT_STATUS, **update}

    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return data


def clear_stop_flag() -> None:
    try:
        stop_path().unlink(missing_ok=True)  # type: ignore[call-arg]
    except TypeError:
        # py3.7 compat style
        p = stop_path()
        if p.exists():
            p.unlink()
    except Exception:
        p = stop_path()
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass


def request_stop() -> None:
    stop_path().write_text("1\n", encoding="utf-8")
    write_status(
        {
            "stop_requested": True,
            "message": "Stoppen aangevraagd, even geduld…",
        }
    )


def stop_requested() -> bool:
    return stop_path().is_file()


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def is_worker_running() -> bool:
    """True if a live ingest worker holds the lock, or status says running with live/recent pid.

    Lock file is authoritative (worker sets it). Status pid alone is not enough for
    double-spawn races during the API→worker handoff.
    """
    path = lock_path()
    if path.exists():
        try:
            old = int(path.read_text(encoding="utf-8").strip() or "0")
        except Exception:
            old = 0
        if old and _pid_alive(old):
            return True

    st = read_status()
    if st.get("status") != "running":
        return False
    pid = st.get("pid")
    if pid and _pid_alive(int(pid)):
        return True
    # Handoff window: API set status=running before worker acquired lock / wrote pid
    started = st.get("started_at")
    if started and not pid:
        try:
            raw = str(started).replace("Z", "+00:00")
            started_dt = datetime.fromisoformat(raw)
            if started_dt.tzinfo is None:
                started_dt = started_dt.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - started_dt).total_seconds()
            if 0 <= age < 45:
                return True
        except Exception:
            return True
    return False


def try_acquire_lock(pid: int) -> bool:
    """Create exclusive lock file with pid. Returns False if another live worker holds it."""
    path = lock_path()
    if path.exists():
        try:
            old = int(path.read_text(encoding="utf-8").strip() or "0")
        except Exception:
            old = 0
        if old and _pid_alive(old):
            return False
        try:
            path.unlink()
        except Exception:
            pass
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(str(pid))
        return True
    except FileExistsError:
        return False
    except Exception:
        return False


def release_lock(pid: int | None = None) -> None:
    path = lock_path()
    if not path.exists():
        return
    try:
        if pid is not None:
            cur = int(path.read_text(encoding="utf-8").strip() or "0")
            if cur and cur != pid:
                return
        path.unlink()
    except Exception:
        pass


def _clear_lock_if_stale() -> None:
    path = lock_path()
    if not path.exists():
        return
    try:
        old = int(path.read_text(encoding="utf-8").strip() or "0")
    except Exception:
        old = 0
    if old and not _pid_alive(old):
        try:
            path.unlink()
        except Exception:
            pass


def new_run_id() -> str:
    return f"{int(time.time())}-{os.getpid()}"
