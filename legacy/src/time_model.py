"""Compatibility re-export for time model (migrated to bandabi.time_model)."""

from bandabi.time_model import TimeModel, build_time_model, haversine_km

__all__ = ["TimeModel", "build_time_model", "haversine_km"]
