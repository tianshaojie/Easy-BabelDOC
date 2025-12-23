import errno
import socket
import logging
from typing import Optional

logger = logging.getLogger("easy_babeldoc")

def get_env_int(name: str, default: int) -> int:
    """Return integer environment variable value with fallback."""
    import os
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning(
            "Environment variable %s=%r is not a valid integer; falling back to %s",
            name,
            value,
            default,
        )
        return default

def determine_host(cli_host: Optional[str] = None) -> str:
    """Determine which host the server should bind to."""
    import os
    if cli_host:
        return cli_host
    env_host = os.environ.get("EASY_BABELDOC_HOST")
    if env_host:
        return env_host
    return "0.0.0.0"

def determine_port(cli_port: Optional[int] = None) -> int:
    """Determine the preferred port for the server."""
    if cli_port is not None:
        return cli_port
    return get_env_int("EASY_BABELDOC_PORT", 58273)

def determine_port_search_limit(cli_limit: Optional[int] = None) -> int:
    """Determine how many additional ports we should probe when encountering conflicts."""
    if cli_limit is not None:
        return max(cli_limit, 0)
    return max(get_env_int("EASY_BABELDOC_PORT_SEARCH_LIMIT", 10), 0)

def can_bind_port(host: str, port: int) -> bool:
    """Check whether the given host/port is currently available for binding."""
    try:
        addr_infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        logger.error("Invalid host %s: %s", host, exc)
        raise SystemExit(1)

    bindable = False
    for family, socktype, proto, _, sockaddr in addr_infos:
        try:
            with socket.socket(family, socktype, proto) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(sockaddr)
                bindable = True
        except OSError as exc:
            if exc.errno == errno.EADDRINUSE:
                return False
            if exc.errno in (errno.EADDRNOTAVAIL, errno.EAFNOSUPPORT):
                continue
            raise

    return bindable
