#!/usr/bin/env python3
"""
trigger.py - Service Keep-Alive Script

TWO modes of operation:
─────────────────────────────────────────────────────────────────────────────
1. EMBEDDED (production — default):
   Imported by main.py and started as a background daemon thread inside the
   FastAPI lifespan.  The service pings its own public URL every 14 minutes,
   keeping the Render free-tier container alive from within.

   main.py calls:
       from trigger import start_keep_alive_thread
       start_keep_alive_thread()

2. STANDALONE (local / testing):
   Run directly as a script:
       python trigger.py
       HEALTH_ENDPOINT=https://prepiq-narg.onrender.com/health python trigger.py
       PING_INTERVAL=10 python trigger.py   # quick test with 10-second interval

─────────────────────────────────────────────────────────────────────────────
Environment variables (both modes):
    HEALTH_ENDPOINT   URL to ping
                      default (standalone) : http://localhost:8000/health
                      default (embedded)   : https://prepiq-narg.onrender.com/health
    PING_INTERVAL     Seconds between pings  (default: 840 = 14 min)
    MAX_RETRIES       Retry attempts per ping (default: 3)
    RETRY_DELAY       Seconds between retries (default: 5)

Additional standalone-only variables:
    LOG_FILE          Log file path  (default: trigger.log)
"""

import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Shared configuration
# ---------------------------------------------------------------------------
PING_INTERVAL: int = int(os.getenv("PING_INTERVAL", "840"))   # 14 minutes
MAX_RETRIES: int   = int(os.getenv("MAX_RETRIES",   "3"))
RETRY_DELAY: int   = int(os.getenv("RETRY_DELAY",   "5"))

# ---------------------------------------------------------------------------
# Standalone-only config
# ---------------------------------------------------------------------------
_STANDALONE_ENDPOINT = os.getenv("HEALTH_ENDPOINT", "http://localhost:8000/health")
_LOG_FILE            = os.getenv("LOG_FILE", "trigger.log")

# ---------------------------------------------------------------------------
# Embedded-mode default — your live Render URL
# This is used when start_keep_alive_thread() is called without arguments.
# ---------------------------------------------------------------------------
_RENDER_ENDPOINT = "https://prepiq-narg.onrender.com/health"


# ---------------------------------------------------------------------------
# Core ping — shared by both modes
# ---------------------------------------------------------------------------

def _ping(url: str, log: logging.Logger) -> bool:
    """
    GET *url* with retry logic.  Returns True on HTTP 200, False otherwise.
    Uses its own logger so it works in both thread and standalone contexts.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(
                url,
                timeout=30,
                headers={"User-Agent": "PrepIQ-KeepAlive/1.0"},
            )
            if resp.status_code == 200:
                log.info(f"[keep-alive] OK — HTTP {resp.status_code}  {url}")
                return True
            log.warning(
                f"[keep-alive] Unexpected {resp.status_code} "
                f"(attempt {attempt}/{MAX_RETRIES})"
            )
        except requests.exceptions.Timeout:
            log.error(f"[keep-alive] Timeout  (attempt {attempt}/{MAX_RETRIES})")
        except requests.exceptions.ConnectionError:
            log.error(f"[keep-alive] Connection error  (attempt {attempt}/{MAX_RETRIES})")
        except requests.exceptions.RequestException as exc:
            log.error(f"[keep-alive] Request error: {exc}  (attempt {attempt}/{MAX_RETRIES})")
        except Exception as exc:
            log.error(f"[keep-alive] Unexpected error: {exc}  (attempt {attempt}/{MAX_RETRIES})")

        if attempt < MAX_RETRIES:
            log.info(f"[keep-alive] Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)

    return False


# ---------------------------------------------------------------------------
# Interruptible sleep — wakes up if the stop event is set
# ---------------------------------------------------------------------------

def _sleep(seconds: int, stop_event: threading.Event) -> None:
    """Sleep for *seconds*, but return early if *stop_event* is set."""
    stop_event.wait(timeout=seconds)


# ---------------------------------------------------------------------------
# Background thread loop
# ---------------------------------------------------------------------------

def _keep_alive_loop(
    url: str,
    stop_event: threading.Event,
    log: logging.Logger,
) -> None:
    """
    Runs as a daemon thread inside the FastAPI process.

    - Pings *url* immediately on start, then every PING_INTERVAL seconds.
    - Stops cleanly when *stop_event* is set (FastAPI shutdown).
    - Never raises — all exceptions are caught and logged so the thread
      can't crash the main application.
    """
    ping_count    = 0
    success_count = 0

    log.info(f"[keep-alive] Thread started — endpoint: {url}  interval: {PING_INTERVAL}s")

    first = True
    while not stop_event.is_set():
        if first:
            first = False
            # Small initial delay so uvicorn finishes binding the port
            # before we try to hit the public URL.
            _sleep(10, stop_event)
        else:
            _sleep(PING_INTERVAL, stop_event)

        if stop_event.is_set():
            break

        ping_count += 1
        log.info(
            f"[keep-alive] Ping #{ping_count}  "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        try:
            ok = _ping(url, log)
            if ok:
                success_count += 1
            else:
                log.warning(
                    f"[keep-alive] Ping #{ping_count} failed  "
                    f"({success_count}/{ping_count} succeeded so far)"
                )
        except Exception as exc:
            log.error(f"[keep-alive] Unhandled error during ping: {exc}", exc_info=True)

    log.info(
        f"[keep-alive] Thread stopped — "
        f"{success_count}/{ping_count} pings succeeded"
    )


# ---------------------------------------------------------------------------
# Public API — called by main.py
# ---------------------------------------------------------------------------

_stop_event: threading.Event = threading.Event()


def start_keep_alive_thread(
    url: str = _RENDER_ENDPOINT,
    logger: logging.Logger | None = None,
) -> threading.Thread:
    """
    Start the keep-alive ping loop as a background daemon thread.

    Parameters
    ----------
    url : str
        The health endpoint to ping.  Defaults to the live Render URL.
    logger : logging.Logger, optional
        Pass the application logger so keep-alive messages appear in the
        same log stream.  Falls back to a module-level logger.

    Returns
    -------
    threading.Thread
        The running daemon thread (usually you can ignore the return value).

    Usage in main.py lifespan
    -------------------------
        from trigger import start_keep_alive_thread, stop_keep_alive_thread

        @asynccontextmanager
        async def lifespan(app):
            start_keep_alive_thread()
            yield
            stop_keep_alive_thread()
    """
    _stop_event.clear()
    log = logger or logging.getLogger(__name__)

    thread = threading.Thread(
        target=_keep_alive_loop,
        args=(url, _stop_event, log),
        name="keep-alive",
        daemon=True,   # dies automatically when the main process exits
    )
    thread.start()
    log.info(f"[keep-alive] Background thread started (daemon=True)")
    return thread


def stop_keep_alive_thread() -> None:
    """
    Signal the keep-alive thread to stop.
    Called from the FastAPI lifespan shutdown block.
    Returns immediately — the thread exits within seconds.
    """
    _stop_event.set()


# ---------------------------------------------------------------------------
# Standalone helpers (only used when running as `python trigger.py`)
# ---------------------------------------------------------------------------

# Global flag for SIGINT/SIGTERM in standalone mode
_standalone_running: bool = True


def _setup_standalone_logging() -> logging.Logger:
    log_path = Path(_LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


def _write_status(status: str, details: dict) -> None:
    status_path = Path(_LOG_FILE).parent / "trigger.status"
    try:
        with open(status_path, "w", encoding="utf-8") as fh:
            json.dump({"timestamp": datetime.now().isoformat(), "status": status, **details}, fh, indent=2)
    except Exception:
        pass


def _standalone_signal_handler(signum: int, frame) -> None:
    global _standalone_running
    print(f"\nReceived signal {signum} — shutting down...")
    _standalone_running = False


def _standalone_main() -> None:
    global _standalone_running

    signal.signal(signal.SIGINT,  _standalone_signal_handler)
    signal.signal(signal.SIGTERM, _standalone_signal_handler)

    log  = _setup_standalone_logging()
    url  = _STANDALONE_ENDPOINT

    log.info("=" * 60)
    log.info("PrepIQ Keep-Alive Trigger  [standalone mode]")
    log.info(f"  Endpoint : {url}")
    log.info(f"  Interval : {PING_INTERVAL}s  ({PING_INTERVAL / 60:.1f} min)")
    log.info(f"  Log file : {_LOG_FILE}")
    log.info("Press Ctrl+C to stop")
    log.info("=" * 60)

    _write_status("starting", {"message": "standalone trigger starting", "endpoint": url})

    ping_count = success_count = failure_count = 0
    first = True

    while _standalone_running:
        try:
            if first:
                first = False
                log.info("Performing initial health check...")
            else:
                log.info(f"Waiting {PING_INTERVAL}s ({PING_INTERVAL / 60:.1f} min)...")
                # interruptible wait
                for _ in range(PING_INTERVAL):
                    if not _standalone_running:
                        break
                    time.sleep(1)

            if not _standalone_running:
                break

            ping_count += 1
            log.info(f"--- Ping #{ping_count}  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")

            ok = _ping(url, log)
            if ok:
                success_count += 1
            else:
                failure_count += 1

            _write_status(
                "healthy" if ok else "unhealthy",
                {
                    "ping_count": ping_count,
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "success_rate": f"{success_count / ping_count * 100:.1f}%",
                    "endpoint": url,
                },
            )

        except Exception as exc:
            log.error(f"Critical error in main loop: {exc}", exc_info=True)
            time.sleep(30)

    rate = f"{success_count / ping_count * 100:.1f}%" if ping_count else "N/A"
    log.info("=" * 60)
    log.info(f"Stopped — {success_count}/{ping_count} pings succeeded  ({rate})")
    log.info("=" * 60)
    _write_status("stopped", {"ping_count": ping_count, "success_count": success_count,
                              "failure_count": failure_count, "reason": "graceful_shutdown"})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        _standalone_main()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt — exiting.")
    except Exception as exc:
        logging.getLogger(__name__).error(f"Fatal error: {exc}", exc_info=True)
        sys.exit(1)
    sys.exit(0)
