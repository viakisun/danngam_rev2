"""지리 좌표 유틸리티 — Haversine 거리 계산."""

import math

EARTH_RADIUS_KM = 6371.0
DEFAULT_RADIUS_KM = 5.0
MAX_RADIUS_KM = 30.0


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """두 좌표 사이의 거리를 km 단위로 계산 (Haversine formula).

    Args:
        lat1: 기준점 위도
        lng1: 기준점 경도
        lat2: 대상점 위도
        lng2: 대상점 경도

    Returns:
        두 점 사이의 거리 (km)
    """
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def is_within_radius(
    center_lat: float,
    center_lng: float,
    target_lat: float,
    target_lng: float,
    radius_km: float = DEFAULT_RADIUS_KM,
) -> bool:
    """대상 좌표가 기준 반경 내에 있는지 확인."""
    distance = haversine(center_lat, center_lng, target_lat, target_lng)
    return distance <= radius_km
