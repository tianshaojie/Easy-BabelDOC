#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy-BabelDOC - 基于BabelDOC API的Web翻译应用
Copyright (C) 2024 lijiapeng365

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

Based on BabelDOC: https://github.com/funstory-ai/BabelDOC
Source code: https://github.com/lijiapeng365/Easy-BabelDOC
"""

import argparse
import errno
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List

from config.settings import FRONTEND_STATIC_DIR, FRONTEND_INDEX_FILE, DATA_DIR
from utils.network import determine_host, determine_port, determine_port_search_limit, can_bind_port

try:
    import babeldoc.format.pdf.high_level as high_level
    high_level.init()
except:
    print("BabelDOC initialization skipped (development mode)")

app = FastAPI(title="BabelDOC API", version="1.0.0")

logger = logging.getLogger("easy_babeldoc")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

logger.info("Using data directory: %s", DATA_DIR)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(404)
async def spa_fallback(request: Request, exc: HTTPException):
    """Serve the React SPA for unknown non-API routes."""
    from pathlib import Path
    path = request.url.path
    if (
        request.method == "GET"
        and FRONTEND_STATIC_DIR.exists()
        and FRONTEND_INDEX_FILE.exists()
        and not path.startswith(("/api", "/docs", "/redoc", "/openapi"))
        and "." not in Path(path).name
    ):
        return FileResponse(FRONTEND_INDEX_FILE)

    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

from api import register_routes
register_routes(app)

def run_server(host: str, preferred_port: int, port_search_limit: int = 10) -> None:
    """Start uvicorn with automatic fallback when the preferred port is occupied."""
    import uvicorn
    attempted_ports: List[int] = []
    for offset in range(port_search_limit + 1):
        port = preferred_port + offset
        attempted_ports.append(port)
        if not can_bind_port(host, port):
            logger.warning("Port %s is in use. Trying next port...", port)
            continue
        try:
            logger.info("Starting Easy-BabelDOC server on %s:%s", host, port)
            uvicorn.run(app, host=host, port=port)
            return
        except OSError as exc:
            if exc.errno != errno.EADDRINUSE:
                raise
            logger.warning("Port %s is in use. Trying next port...", port)
            continue

    min_port = attempted_ports[0]
    max_port = attempted_ports[-1]
    logger.error(
        "Unable to find an open port in range %s-%s. "
        "Set EASY_BABELDOC_PORT or use --port to pick a different starting port.",
        min_port,
        max_port,
    )
    raise SystemExit(1)

if FRONTEND_STATIC_DIR.exists():
    logger.info("Serving frontend assets from %s", FRONTEND_STATIC_DIR)
    app.mount("/", StaticFiles(directory=str(FRONTEND_STATIC_DIR), html=True), name="frontend")
else:
    logger.warning(
        "Frontend build not found at %s. Only API routes will be available.",
        FRONTEND_STATIC_DIR,
    )

    @app.get("/", include_in_schema=False)
    async def root_placeholder():
        return {
            "message": "BabelDOC API Server",
            "version": "1.0.0",
            "frontend_ready": False,
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Easy-BabelDOC backend server.")
    parser.add_argument("--host", help="Host/IP to bind (default: EASY_BABELDOC_HOST or 0.0.0.0)")
    parser.add_argument(
        "--port",
        type=int,
        help="Preferred port (default: EASY_BABELDOC_PORT or 8000)",
    )
    parser.add_argument(
        "--port-search-limit",
        type=int,
        help="How many additional ports to probe when the preferred port is occupied "
        "(default: EASY_BABELDOC_PORT_SEARCH_LIMIT or 10).",
    )
    cli_args = parser.parse_args()

    host = determine_host(cli_args.host)
    port = determine_port(cli_args.port)
    port_search_limit = determine_port_search_limit(cli_args.port_search_limit)

    logger.info(
        "Starting Easy-BabelDOC with host=%s port=%s (search limit: %s)",
        host,
        port,
        port_search_limit,
    )

    run_server(host, port, port_search_limit)
