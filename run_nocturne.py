#!/usr/bin/env python3
"""Small launcher that prints Nocturne's local URL and starts Uvicorn.

You can still run `python -m uvicorn main:app ...` directly. This wrapper exists
for friendlier alpha/tester launches: it passes the host/port into the app so the
startup log can print a copyable "Nocturne is ready at ..." line.
"""
from __future__ import annotations

import argparse
import os

import uvicorn


def main() -> int:
    parser = argparse.ArgumentParser(description="Start the local Nocturne server.")
    parser.add_argument("--host", default=os.getenv("NOCTURNE_HOST", "127.0.0.1"), help="bind host; use 0.0.0.0 for trusted-LAN access")
    parser.add_argument("--port", type=int, default=int(os.getenv("NOCTURNE_PORT", "8000")), help="bind port")
    parser.add_argument("--reload", action="store_true", help="enable Uvicorn auto-reload for development")
    args = parser.parse_args()

    os.environ["NOCTURNE_HOST"] = args.host
    os.environ["NOCTURNE_PORT"] = str(args.port)

    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
