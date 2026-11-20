"""Esup-Pod helpers for Runner warnings stored in existing task and encoding logs."""

import json

WARNINGS_LOG_PREFIX = "Runner manager warnings: "


def normalize_runner_warnings(value: object) -> list[str] | None:
    """Normalize a warning list received from the Runner.

    Args:
        value: Raw warnings value from a Runner payload.

    Returns:
        Distinct, stripped, nonempty strings, or None if value is not a list.
    """
    if not isinstance(value, list):
        return None
    return list(
        dict.fromkeys(
            message.strip()
            for message in value
            if isinstance(message, str) and message.strip()
        )
    )


def format_runner_warnings(warnings: list[str]) -> str:
    """Serialize diagnostics on one log line, preserving multiline messages.

    Args:
        warnings: Normalized warning messages to record.

    Returns:
        A prefixed JSON log entry that read_runner_warnings can decode.
    """
    return WARNINGS_LOG_PREFIX + json.dumps(warnings)


def read_runner_warnings(output: str | None) -> list[str]:
    """Read the latest warning list explicitly recorded in a log.

    Args:
        output: Existing task script output or video encoding log, if available.

    Returns:
        The latest valid warning list, or an empty list if none was recorded.
        Malformed entries and ordinary log messages are ignored.
    """
    for line in reversed((output or "").splitlines()):
        if not line.startswith(WARNINGS_LOG_PREFIX):
            continue
        try:
            value = json.loads(line[len(WARNINGS_LOG_PREFIX) :])
        except ValueError:
            continue
        warnings = normalize_runner_warnings(value)
        if warnings is not None:
            return warnings
    return []
