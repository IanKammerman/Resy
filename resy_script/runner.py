import re
import time
from typing import List, Optional

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

from .config import ResyConfig


def _safe_click_first(page: Page, selectors: List[str], timeout_ms: int) -> bool:
    for selector in selectors:
        try:
            locator = page.locator(selector)
            if locator.first.is_visible(timeout=timeout_ms):
                locator.first.click()
                return True
        except Exception:
            continue
    return False


def _login(page: Page, config: ResyConfig) -> None:
    page.goto("https://resy.com/login", wait_until="networkidle")

    # Try multiple strategies to fill email and password
    email_locators = [
        'input[type="email"]',
        'input[name="email"]',
        'input[autocomplete="email"]',
        'input[placeholder*="Email" i]'
    ]
    password_locators = [
        'input[type="password"]',
        'input[name="password"]',
        'input[autocomplete="current-password"]',
        'input[placeholder*="Password" i]'
    ]

    filled = False
    for e_sel in email_locators:
        for p_sel in password_locators:
            try:
                page.locator(e_sel).first.fill(config.email, timeout=config.timeout_ms)
                page.locator(p_sel).first.fill(config.password, timeout=config.timeout_ms)
                filled = True
                break
            except Exception:
                continue
        if filled:
            break

    # Click a submit button
    _ = _safe_click_first(
        page,
        [
            'button:has-text("Log In")',
            'button:has-text("Sign In")',
            'button[type="submit"]',
            'button[aria-label*="Log" i]'
        ],
        config.timeout_ms,
    )

    # Wait for navigation or evidence of a logged-in state
    try:
        page.wait_for_load_state("networkidle", timeout=config.timeout_ms)
    except PlaywrightTimeoutError:
        pass


def _build_venue_url_with_params(config: ResyConfig) -> str:
    separator = "&" if "?" in config.venue_url else "?"
    return f"{config.venue_url}{separator}seats={config.party_size}&date={config.date}"


def _find_time_buttons(page: Page) -> List[str]:
    # Collect selectors for buttons that look like times
    time_button_selectors = []

    # Common time buttons often contain AM/PM text
    candidates = page.locator("button").all_text_contents()
    time_pattern = re.compile(r"\b\d{1,2}[:\.]\d{2}\s?(AM|PM)\b", re.I)
    for idx, text in enumerate(candidates):
        if time_pattern.search(text or ""):
            time_button_selectors.append(f"button:has-text(\"{text.strip()}\")")

    # Add probable test ids if present
    time_button_selectors.extend([
        '[data-testid="time-slot"]',
        '[data-test="time-slot"]',
    ])

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for s in time_button_selectors:
        if s not in seen:
            seen.add(s)
            deduped.append(s)
    return deduped


def _click_desired_time(page: Page, config: ResyConfig) -> bool:
    # If exact time requested, try that first
    if config.time_preference and config.exact_time:
        selectors = [f'button:has-text("{config.time_preference}")']
        if _safe_click_first(page, selectors, config.timeout_ms):
            return True

    # Otherwise, choose closest at/after the preferred time or earliest
    time_buttons = page.locator("button").all_text_contents()
    time_pattern = re.compile(r"\b\d{1,2}[:\.]\d{2}\s?(AM|PM)\b", re.I)
    times = [t.strip() for t in time_buttons if time_pattern.search((t or "").strip())]

    if not times:
        return False

    def parse_time_to_minutes(s: str) -> int:
        m = re.match(r"^(\d{1,2})[:\.]?(\d{2})?\s*(AM|PM)$", s.strip(), re.I)
        if not m:
            # Try common format like 7:30 PM
            m = re.match(r"^(\d{1,2}):(\d{2})\s*(AM|PM)$", s.strip(), re.I)
        if not m:
            return 0
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        ap = m.group(3).upper()
        if hour == 12:
            hour = 0
        total = hour * 60 + minute
        if ap == "PM":
            total += 12 * 60
        return total

    desired_minutes: Optional[int] = None
    if config.time_preference:
        try:
            desired_minutes = parse_time_to_minutes(config.time_preference)
        except Exception:
            desired_minutes = None

    chosen_text: Optional[str] = None
    if desired_minutes is not None:
        # pick the smallest time >= desired
        viable = sorted((t for t in times), key=parse_time_to_minutes)
        for t in viable:
            if parse_time_to_minutes(t) >= desired_minutes:
                chosen_text = t
                break
        if not chosen_text:
            # fallback to last available
            chosen_text = viable[-1]
    else:
        # earliest available
        chosen_text = sorted(times, key=parse_time_to_minutes)[0]

    if not chosen_text:
        return False

    return _safe_click_first(page, [f'button:has-text("{chosen_text}")'], config.timeout_ms)


def _complete_booking(page: Page, config: ResyConfig) -> bool:
    # Try a sequence of common booking steps
    steps = [
        ['button:has-text("Book Now")', 'button:has-text("Reserve")'],
        ['button:has-text("Continue")', 'button:has-text("Next")'],
        ['button:has-text("Confirm")', 'button:has-text("Complete")', 'button:has-text("Pay")'],
    ]

    for group in steps:
        clicked = _safe_click_first(page, group, config.timeout_ms)
        if clicked:
            try:
                page.wait_for_load_state("networkidle", timeout=config.timeout_ms)
            except PlaywrightTimeoutError:
                pass

    # Heuristic success checks
    success_markers = [
        "Reservation Confirmed",
        "You're booked",
        "Confirmation",
        "Thanks for booking",
    ]
    content = page.content()
    if any(marker in content for marker in success_markers):
        return True

    # Also consider URL change to a confirmation path as success
    url = page.url
    if any(k in url for k in ["confirmation", "confirm", "success"]):
        return True

    return False


def attempt_reservation(config: ResyConfig) -> bool:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.headless)
        context = browser.new_context()
        page = context.new_page()

        _login(page, config)

        target_url = _build_venue_url_with_params(config)
        deadline = time.time() + (config.max_poll_minutes * 60)

        while True:
            page.goto(target_url, wait_until="networkidle")

            # Some pages need user to set party size/date on page; URL params should help but try to click if needed
            # Attempt to click a desired time
            if _click_desired_time(page, config):
                if _complete_booking(page, config):
                    return True

            if time.time() >= deadline:
                return False

            time.sleep(config.poll_interval_sec)
            try:
                page.reload(wait_until="networkidle")
            except PlaywrightTimeoutError:
                pass

        # Not reachable
        # return False

