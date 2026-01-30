#!/usr/bin/env python3
"""
wait_for_db.py

Wait until the Django default database connection is available.

This script prints progress messages to stderr so they can be streamed
by Docker logs in real time.

Exit codes:
    0 - Database is reachable
    1 - Database is not reachable after all retries
"""

import sys
import time
from django.db import connections
from django.db.utils import OperationalError

MAX_TRIES = 30
SLEEP_SECONDS = 1


def main() -> None:
    """
    Attempt to connect to the database until successful or until
    MAX_TRIES is reached.
    """
    for attempt in range(1, MAX_TRIES + 1):
        try:
            connections["default"].cursor()
            print("[Python] Database connection successful.")
            sys.exit(0)
        except OperationalError:
            print(
                f"[Python] Database not ready "
                f"(attempt {attempt}/{MAX_TRIES})...",
                file=sys.stderr,
            )
            time.sleep(SLEEP_SECONDS)

    print(
        "[Python] Database connection failed after maximum retries.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
