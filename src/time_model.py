# time_model.py
import math
import numpy as np

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

class TimeModel:
    def __init__(self, cfg):
        self.default_speed = cfg["time_model"].get("default_speed_kmh", 18.0)
        self.speed_mult = cfg["time_model"].get("speed_multiplier", 1.0)
        self.detour = cfg["sim"].get("detour_factor", 1.25)
        self.noise_sigma = cfg["sim"].get("travel_time_noise_sigma", 0.25)
    
    def mean_travel_min(self, lat1, lon1, lat2, lon2):
        km = haversine_km(lat1, lon1, lat2, lon2) * self.detour
        speed = self.default_speed * self.speed_mult
        return (km / speed) * 60  # minutes
    
    def sample_travel_min(self, lat1, lon1, lat2, lon2):
        mean = self.mean_travel_min(lat1, lon1, lat2, lon2)
        noise = np.random.randn() * self.noise_sigma * mean
        return max(0.1, mean + noise)

def build_time_model(cfg):
    return TimeModel(cfg)

import os, json, math, datetime
import numpy as np

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

class TimeModel:
    """
    MVP: 직선거리 * detour_factor / (speed_kmh * multiplier)
    promise_time: 평균(노이즈 없음)
    actual_time: 평균 * lognormal_noise (sigma)
    """
    def __init__(self, default_speed_kmh: float, speed_multiplier: float, detour_factor: float, noise_sigma: float):
        self.default_speed_kmh = float(default_speed_kmh)
        self.speed_multiplier = float(speed_multiplier)
        self.detour_factor = float(detour_factor)
        self.noise_sigma = float(noise_sigma)
        self.rng = np.random.default_rng(123)

    def mean_travel_min(self, a_lat, a_lon, b_lat, b_lon):
        dist_km = haversine_km(a_lat, a_lon, b_lat, b_lon) * self.detour_factor
        speed = max(1e-6, self.default_speed_kmh * self.speed_multiplier)
        hours = dist_km / speed
        return hours * 60.0

    def sample_travel_min(self, a_lat, a_lon, b_lat, b_lon):
        mu = self.mean_travel_min(a_lat, a_lon, b_lat, b_lon)
        if self.noise_sigma <= 0:
            return mu
        # lognormal with mean approx = mu (간단 근사)
        noise = self.rng.lognormal(mean=-0.5*self.noise_sigma**2, sigma=self.noise_sigma)
        return float(mu * noise)

def build_time_model(cfg: dict) -> TimeModel:
    base = cfg["time_model"]
    detour = cfg["sim"]["detour_factor"]
    sigma = cfg["sim"]["travel_time_noise_sigma"]
    return TimeModel(
        default_speed_kmh=base["default_speed_kmh"],
        speed_multiplier=base.get("speed_multiplier", 1.0),
        detour_factor=detour,
        noise_sigma=sigma
    )
