#!/usr/bin/env python3
"""Small launcher that prints Nocturne's local URL and starts Uvicorn.

You can still run `python -m uvicorn main:app ...` directly. This wrapper exists
for friendlier alpha/tester launches: it passes the host/port into the app so the
startup log can print a copyable "Nocturne is ready at ..." line.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import uvicorn


def main() -> int:
    parser = argparse.ArgumentParser(description="Start the local Nocturne server.")
    parser.add_argument("--host", default=os.getenv("NOCTURNE_HOST", "127.0.0.1"), help="bind host; use 0.0.0.0 for trusted-LAN access")
    parser.add_argument("--port", type=int, default=int(os.getenv("NOCTURNE_PORT", "8000")), help="bind port")
    parser.add_argument("--reload", action="store_true", help="enable Uvicorn auto-reload for development")
    parser.add_argument(
        "--profile",
        choices=("nocturne", "nocturne-pi"),
        default=os.getenv("NOCTURNE_PROFILE"),
        help="presentation profile; packaged editions set a default in nocturne_profile.json",
    )
    parser.add_argument(
        "--ssl-certfile",
        default=os.getenv("NOCTURNE_SSL_CERTFILE"),
        help="optional trusted/local TLS certificate (pair with --ssl-keyfile)",
    )
    parser.add_argument(
        "--ssl-keyfile",
        default=os.getenv("NOCTURNE_SSL_KEYFILE"),
        help="optional TLS private key (pair with --ssl-certfile)",
    )
    args = parser.parse_args()

    if bool(args.ssl_certfile) != bool(args.ssl_keyfile):
        parser.error("--ssl-certfile and --ssl-keyfile must be supplied together")
    for label, value in (("certificate", args.ssl_certfile), ("private key", args.ssl_keyfile)):
        if value and not Path(value).expanduser().is_file():
            parser.error(f"TLS {label} does not exist: {value}")

    if args.profile:
        os.environ["NOCTURNE_PROFILE"] = args.profile
    os.environ["NOCTURNE_HOST"] = args.host
    os.environ["NOCTURNE_PORT"] = str(args.port)
    os.environ["NOCTURNE_SCHEME"] = "https" if args.ssl_certfile else "http"

    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        ssl_certfile=str(Path(args.ssl_certfile).expanduser()) if args.ssl_certfile else None,
        ssl_keyfile=str(Path(args.ssl_keyfile).expanduser()) if args.ssl_keyfile else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
