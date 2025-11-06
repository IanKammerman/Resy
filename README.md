# Resy Reservation Script (Python + Playwright)

Automates attempting a reservation on Resy for a specified venue, date, party size, and time.

## Setup

1) Python 3.9+ recommended. Create a venv (optional):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies:

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

3) Configure environment variables (copy and edit):

```bash
cp env.example .env
```

Then edit `.env` and fill in your details.

## Usage

You can use CLI flags or rely on `.env` values. CLI flags override `.env`.

Examples:

```bash
# Using .env only
python resy.py

# Override some values via CLI
python resy.py \
  --email "you@example.com" \
  --password "your-password" \
  --venue-url "https://resy.com/cities/ny/your-restaurant" \
  --date 2025-11-07 \
  --party-size 2 \
  --time "7:00 PM" \
  --exact-time \
  --no-headless \
  --max-poll-minutes 10
```

Flags:

- `--email`, `--password`: Resy credentials
- `--venue-url`: Full venue page URL
- `--date`: YYYY-MM-DD
- `--party-size`: integer
- `--time`: preferred time string like `"7:30 PM"`
- `--exact-time`: require exact match
- `--headless`/`--no-headless`: show/hide browser (default headless)
- `--poll-interval`: seconds between refresh attempts (default 2)
- `--max-poll-minutes`: how long to keep trying (default 5)
- `--timeout-ms`: per-step timeout (default 120000)

Environment variables (in `.env`):

- `RESY_EMAIL`, `RESY_PASSWORD`
- `RESY_VENUE_URL`
- `RESY_DATE` (YYYY-MM-DD)
- `RESY_PARTY_SIZE`
- `RESY_TIME_PREFERENCE`
- `RESY_EXACT_TIME` (true/false)
- `RESY_HEADLESS` (true/false)
- `RESY_POLL_INTERVAL_SEC`
- `RESY_MAX_POLL_MINUTES`
- `RESY_TIMEOUT_MS`

## Notes

- Keep a saved payment method in your Resy account for smoother checkout.
- If you encounter selector issues, you may need to tweak the heuristics in `resy_script/runner.py`.
- Use `--no-headless` to visualize and debug the flow.
- Use responsibly and in accordance with Resy's terms of service.
