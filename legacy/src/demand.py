"""Compatibility re-export for demand module (migrated to bandabi.demand)."""

from bandabi.demand import DemandConfig, build_requests, load_centers

__all__ = ["DemandConfig", "build_requests", "load_centers"]
