"""
Esup-Pod - File utility functions.
"""

import os


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
