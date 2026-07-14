"""Aggregates all API routers for the application.

Previously this module wrapped `api.api_router` inside a second, brand new
`APIRouter` just to re-export it under the same name -- that extra layer did
nothing useful. It now re-exports the router directly.
"""

from api import api_router

__all__ = ["api_router"]
