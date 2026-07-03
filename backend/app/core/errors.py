"""Domain-level exceptions.

Services raise these; the API layer maps them to HTTP responses. Keeping them
free of HTTP concerns preserves the dependency direction (services never import
FastAPI).
"""

from __future__ import annotations


class BrewIQError(Exception):
    """Base class for all domain errors."""


class NotFoundError(BrewIQError):
    """A requested entity does not exist."""


class ConflictError(BrewIQError):
    """The operation conflicts with existing state (e.g. duplicate slug)."""
