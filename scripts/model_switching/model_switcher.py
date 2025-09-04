"""Shim that re-exports the model switching utilities from the new location.

Some tests and legacy tooling import `scripts.model_switching.model_switcher`.
To remain backward compatible we re-export the functions and classes from
``scripts.models.model_switcher`` here.
"""

from scripts.models.model_switcher import *  # noqa: F403
