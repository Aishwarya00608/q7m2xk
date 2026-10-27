"""
Elexon BMRS API client.

Endpoints used:
  - FUELHH/stream: Actual half-hourly fuel generation by type
    Filter by settlementDateFrom / settlementDateTo
    Response: [{dataset, publishTime, startTime, settlementDate, settlementPeriod, fuelType, generation}]

  - WINDFOR/stream: Wind generation forecasts
    Filter by publishDateTimeFrom / publishDateTimeTo
    Response: [{dataset, publishTime, startTime, generation}]
    Resolution: 1-hour startTime intervals
    Multiple publishTimes per startTime (forecast revisions)
"""
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Simple in-memory cache: key -> (data, timestamp)
_cache: dict[str, tuple[Any, float]] = {}


def _cache_get(key: str) -> Any | None:
    if key in _cache:
        data, ts = _cache[key]
        if time.time() - ts < settings.CACHE_TTL_SECONDS:
            return data
        del _cache[key]
    return None


def _cache_set(key: str, data: Any) -> None:
    _cache[key] = (data, time.time())


def clear_cache() -> None:
    """Clear all cached data (used by refresh endpoint)."""
    _cache.clear()


def _build_client() -> httpx.Client:
    return httpx.Client(
        base_url=settings.ELEXON_BASE_URL,
        timeout=settings.ELEXON_TIMEOUT,
        headers={"Accept": "application/json"},
    )


def fetch_fuelhh_wind(
    settlement_date_from: str,
    settlement_date_to: str,
) -> list[dict]:
    """
    Fetch actual wind generation from FUELHH/stream.
    
    Args:
        settlement_date_from: Date string 'YYYY-MM-DD' (inclusive)
        settlement_date_to:   Date string 'YYYY-MM-DD' (inclusive)
    
    Returns:
        List of raw FUELHH records with fuelType == 'WIND'.
    """
    cache_key = f"fuelhh_wind_{settlement_date_from}_{settlement_date_to}"
    cached = _cache_get(cache_key)
    if cached is not None:
        logger.info("FUELHH cache hit for %s to %s", settlement_date_from, settlement_date_to)
        return cached

    params = {
        "fuelType": "WIND",
        "settlementDateFrom": settlement_date_from,
        "settlementDateTo": settlement_date_to,
        "format": "json",
    }

    logger.info(
        "Fetching FUELHH WIND from %s to %s",
        settlement_date_from,
        settlement_date_to,
    )

    try:
        with _build_client() as client:
            response = client.get("/datasets/FUELHH/stream", params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        logger.error("FUELHH HTTP error %s: %s", exc.response.status_code, exc.response.text)
        raise
    except httpx.RequestError as exc:
        logger.error("FUELHH request error: %s", exc)
        raise

    if not isinstance(data, list):
        logger.warning("FUELHH unexpected response type: %s", type(data))
        return []

    # Filter to WIND only (defensive, already filtered by API param)
    wind_records = [r for r in data if r.get("fuelType") == "WIND"]
    logger.info("FUELHH returned %d WIND records", len(wind_records))

    _cache_set(cache_key, wind_records)
    return wind_records


def fetch_windfor(
    publish_from: str,
    publish_to: str,
) -> list[dict]:
    """
    Fetch wind generation forecasts from WINDFOR/stream.
    
    The WINDFOR endpoint returns ALL forecast versions published in the
    specified publishDateTime range. Each startTime may have many
    publishTime entries (forecast revisions).
    
    Args:
        publish_from: ISO datetime string for publishDateTimeFrom
        publish_to:   ISO datetime string for publishDateTimeTo
    
    Returns:
        List of raw WINDFOR records.
    """
    cache_key = f"windfor_{publish_from}_{publish_to}"
    cached = _cache_get(cache_key)
    if cached is not None:
        logger.info("WINDFOR cache hit for %s to %s", publish_from, publish_to)
        return cached

    params = {
        "publishDateTimeFrom": publish_from,
        "publishDateTimeTo": publish_to,
        "format": "json",
    }

    logger.info(
        "Fetching WINDFOR published between %s and %s",
        publish_from,
        publish_to,
    )

    try:
        with _build_client() as client:
            response = client.get("/datasets/WINDFOR/stream", params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        logger.error("WINDFOR HTTP error %s: %s", exc.response.status_code, exc.response.text)
        raise
    except httpx.RequestError as exc:
        logger.error("WINDFOR request error: %s", exc)
        raise

    if not isinstance(data, list):
        logger.warning("WINDFOR unexpected response type: %s", type(data))
        return []

    logger.info("WINDFOR returned %d records", len(data))
    _cache_set(cache_key, data)
    return data


def fetch_windfor_for_january_2026() -> list[dict]:
    """
    Fetch all WINDFOR forecasts relevant to January 2026 delivery periods.

    Strategy: We need forecasts published up to the configured cutoff on
    the day before Jan 31 delivery. The lower bound includes the preceding
    day so Jan 1 delivery can use all relevant revisions.
    
    The API uses a publish-time window rather than page/offset pagination.
    """
    publish_from = "2025-12-31T00:00:00Z"
    publish_to = (
        f"2026-01-30T{settings.DAY_AHEAD_CUTOFF_HOUR_UTC:02d}:"
        f"{settings.DAY_AHEAD_CUTOFF_MINUTE_UTC:02d}:00Z"
    )
    return fetch_windfor(publish_from=publish_from, publish_to=publish_to)


def fetch_fuelhh_wind_january_2026() -> list[dict]:
    """Fetch FUELHH WIND actuals for all of January 2026."""
    return fetch_fuelhh_wind(
        settlement_date_from="2026-01-01",
        settlement_date_to="2026-01-31",
    )
