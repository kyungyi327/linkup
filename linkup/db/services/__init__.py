"""
services/  (business-logic layer)

Services combine multiple DAOs to implement features that span tables.
They are stateless except for the DAOs they hold.

Implementation status (v2, 2026-05-16):
    routine_service.py — skeleton (NotImplementedError)
"""

from .routine_service import RoutineService

__all__ = ["RoutineService"]
