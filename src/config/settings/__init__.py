"""
Settings package initialization.

Aggregates specialized configuration modules for Authentication and Swagger
to make them easily accessible.
"""
from .authentication import *  # noqa: F401, F403
from .swagger import *  # noqa: F401, F403
