"""
API package for Charon firewall.

This package provides a RESTful API for external applications to interact with the firewall.
"""

from .api import app, run_api

__all__ = ['app', 'run_api'] 