"""
Connectivity monitor using AnyBar.

Launches AnyBar on a random port and pings `target` every `interval` seconds.
The AnyBar icon reflects reachability:
  filled      → internet reachable
  exclamation → no connection
  hollow      → shutting down

Configuration file (all keys optional):
  $XDG_CONFIG_HOME/pingtray/config.toml   (default: ~/.config/pingtray/config.toml)

  target        = "1.1.1.1"
  interval      = 1.0
  anybar_binary = "/Applications/AnyBar.app/Contents/MacOS/AnyBar"
  log_level     = "WARNING"   # DEBUG, INFO, WARNING, ERROR
"""

import asyncio
import logging
import os
import signal
import socket
import tomllib
from pathlib import Path

from icmplib import async_ping


def _load_config() -> dict:
    xdg = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    path = xdg / "pingtray" / "config.toml"
    if path.exists():
        with path.open("rb") as f:
            return tomllib.load(f)
    return {}


config = _load_config()

logging.basicConfig(
    level=config.get("log_level", "WARNING").upper(),
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

ANYBAR_BINARY = config.get(
    "anybar_binary", "/Applications/AnyBar.app/Contents/MacOS/AnyBar"
)
PING_TARGET = config.get("target", "1.1.1.1")
INTERVAL = float(config.get("interval", 1))


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def anybar_send(port: int, command: str) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(command.encode(), ("127.0.0.1", port))


async def reachable() -> bool:
    host = await async_ping(PING_TARGET, count=1, timeout=1, privileged=False)
    return host.is_alive


async def main() -> None:
    port = free_port()
    bar = await asyncio.create_subprocess_exec(
        ANYBAR_BINARY,
        env={**os.environ, "ANYBAR_PORT": str(port)},
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    logger.debug("AnyBar started on port %s (PID %s)", port, bar.pid)
    await asyncio.sleep(0.5)  # let AnyBar initialize

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()

    def on_signal() -> None:
        if not stop.is_set():
            logger.debug("Shutting down")
            stop.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, on_signal)

    last: str | None = None

    while not stop.is_set():
        connected = await reachable()
        state = "filled" if connected else "exclamation"
        if state != last:
            anybar_send(port, state)
            label = "connected" if connected else "no connection"
            logger.debug("[%s] → %s", label, state)
            last = state
        try:
            await asyncio.wait_for(stop.wait(), timeout=INTERVAL)
        except TimeoutError:
            pass

    try:
        bar.terminate()
    except ProcessLookupError:
        pass
    await bar.wait()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
