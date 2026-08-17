"""
Esup-Pod - File utility functions.
"""

import logging
import os
from time import sleep

logger = logging.getLogger(__name__)


def safe_remove_file(field) -> None:
    """
    Safely deletes a file from disk if it exists.
    Handles ValueError when field is empty/null or path is invalid.
    """
    if field:
        try:
            if os.path.isfile(field.path):
                os.remove(field.path)
        except ValueError:
            pass


def check_size_not_changing(
    resource_path: str, max_attempt: int = 10
) -> None:
    """
    Check if the size of a resource remains unchanged over a number of attempts.

    Raises:
        Exception: if the file size keeps changing after max_attempt retries.
        OSError: if the resource does not exist or is inaccessible.
    """
    file_size = os.path.getsize(resource_path)
    size_match = False
    attempt_number = 0

    while not size_match and attempt_number <= max_attempt:
        sleep(1)
        new_size = os.path.getsize(resource_path)
        if file_size != new_size:
            logger.warning(
                "File size of %s changing from %s to %s, attempt number %s",
                resource_path,
                file_size,
                new_size,
                attempt_number,
            )
            file_size = new_size
            attempt_number += 1
            if attempt_number == max_attempt:
                logger.error("File: %s is still changing", resource_path)
                raise Exception("checkFileSize aborted")
        else:
            logger.info("Size checked for %s: %s", resource_path, new_size)
            size_match = True


def check_exists(
    resource_path: str, is_dir: bool, max_attempt: int = 10
) -> None:
    """
    Check whether a file or directory exists, retrying up to max_attempt times.

    Args:
        resource_path: resource path and name.
        is_dir: True for a dir, False for a file.
        max_attempt: number of attempts before raising.
    Raises:
        Exception: if the resource doesn't exist after max_attempt retries.
    """
    fct = os.path.isdir if is_dir else os.path.exists
    r_type = "Dir" if is_dir else "File"
    attempt_number = 1

    while not fct(resource_path) and attempt_number <= max_attempt:
        logger.warning("%s does not exist, attempt number %s", r_type, attempt_number)
        if attempt_number == max_attempt:
            logger.error("Impossible to get %s: %s", r_type, resource_path)
            raise Exception(f"{r_type}: {resource_path} does not exist")
        attempt_number += 1
        sleep(1)


def check_dir_exists(dest_dir_name: str, max_attempt: int = 10) -> None:
    """Check a directory exists, retrying if needed."""
    return check_exists(dest_dir_name, True, max_attempt)


def check_file_exists(full_file_name: str, max_attempt: int = 10) -> None:
    """Check a file exists, retrying if needed."""
    return check_exists(full_file_name, False, max_attempt)
