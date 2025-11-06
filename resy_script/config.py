from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class ResyConfig:
    email: str
    password: str
    venue_url: str
    date: str  # YYYY-MM-DD
    party_size: int
    time_preference: Optional[str] = None  # e.g., "7:00 PM"
    exact_time: bool = False
    headless: bool = True
    poll_interval_sec: int = 2
    max_poll_minutes: int = 5
    timeout_ms: int = 120000

    @staticmethod
    def from_env() -> "ResyConfig":
        email = os.getenv("RESY_EMAIL", "").strip()
        password = os.getenv("RESY_PASSWORD", "").strip()
        venue_url = os.getenv("RESY_VENUE_URL", "").strip()
        date = os.getenv("RESY_DATE", "").strip()
        party_size_str = os.getenv("RESY_PARTY_SIZE", "2").strip()
        time_pref = os.getenv("RESY_TIME_PREFERENCE", "").strip() or None
        exact_time = os.getenv("RESY_EXACT_TIME", "false").strip().lower() in {"1", "true", "yes", "y"}
        headless = os.getenv("RESY_HEADLESS", "true").strip().lower() in {"1", "true", "yes", "y"}
        poll_interval_sec = int(os.getenv("RESY_POLL_INTERVAL_SEC", "2").strip())
        max_poll_minutes = int(os.getenv("RESY_MAX_POLL_MINUTES", "5").strip())
        timeout_ms = int(os.getenv("RESY_TIMEOUT_MS", "120000").strip())

        try:
            party_size = int(party_size_str)
        except ValueError:
            party_size = 2

        return ResyConfig(
            email=email,
            password=password,
            venue_url=venue_url,
            date=date,
            party_size=party_size,
            time_preference=time_pref,
            exact_time=exact_time,
            headless=headless,
            poll_interval_sec=poll_interval_sec,
            max_poll_minutes=max_poll_minutes,
            timeout_ms=timeout_ms,
        )

