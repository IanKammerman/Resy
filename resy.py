import argparse
import sys
from dotenv import load_dotenv

from resy_script.config import ResyConfig
from resy_script.runner import attempt_reservation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automate a Resy reservation.")
    parser.add_argument("--email", help="Resy account email")
    parser.add_argument("--password", help="Resy account password")
    parser.add_argument("--venue-url", help="Full Resy venue URL, e.g., https://resy.com/cities/ny/restaurant")
    parser.add_argument("--date", help="Reservation date YYYY-MM-DD")
    parser.add_argument("--party-size", type=int, default=2, help="Party size, e.g., 2")
    parser.add_argument("--time", dest="time_preference", help='Preferred time like "7:30 PM"')
    parser.add_argument("--exact-time", action="store_true", help="Require exact time match")
    parser.add_argument("--headless", action="store_true", help="Run browser headless (default)")
    parser.add_argument("--no-headless", dest="headless", action="store_false", help="Run with visible browser")
    parser.add_argument("--poll-interval", type=int, default=2, help="Seconds between refresh attempts")
    parser.add_argument("--max-poll-minutes", type=int, default=5, help="Max minutes to keep polling")
    parser.add_argument("--timeout-ms", type=int, default=120000, help="Per-step timeout in milliseconds")
    parser.set_defaults(headless=True)
    return parser


def main(argv=None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)

    cfg = ResyConfig.from_env()

    # Override with CLI args if provided
    if args.email:
        cfg.email = args.email
    if args.password:
        cfg.password = args.password
    if args.venue_url:
        cfg.venue_url = args.venue_url
    if args.date:
        cfg.date = args.date
    if args.party_size:
        cfg.party_size = args.party_size
    if args.time_preference:
        cfg.time_preference = args.time_preference
    if args.exact_time:
        cfg.exact_time = True
    cfg.headless = args.headless
    if args.poll_interval:
        cfg.poll_interval_sec = args.poll_interval
    if args.max_poll_minutes:
        cfg.max_poll_minutes = args.max_poll_minutes
    if args.timeout_ms:
        cfg.timeout_ms = args.timeout_ms

    missing = []
    if not cfg.email:
        missing.append("--email or RESY_EMAIL")
    if not cfg.password:
        missing.append("--password or RESY_PASSWORD")
    if not cfg.venue_url:
        missing.append("--venue-url or RESY_VENUE_URL")
    if not cfg.date:
        missing.append("--date or RESY_DATE")

    if missing:
        parser.error("Missing required: " + ", ".join(missing))

    ok = attempt_reservation(cfg)
    if ok:
        print("Reservation attempt reported success.")
        return 0
    print("Reservation not completed within the allotted time.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

