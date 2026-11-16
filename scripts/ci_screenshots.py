"""
Take screenshots of every page and save each page's HTML for validation.
Runs in GitHub Actions against a local runserver filled with ci_demo_data.py.
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
DEMO = json.loads(pathlib.Path("ci-demo.json").read_text())
SHOTS = pathlib.Path("docs/screenshots")
HTML = pathlib.Path("docs/testing/html")
SHOTS.mkdir(parents=True, exist_ok=True)
HTML.mkdir(parents=True, exist_ok=True)

DESKTOP = {"width": 1366, "height": 900}
MOBILE = {"width": 390, "height": 844}


def capture(page, name, url=None, mobile_too=False, wait_for=None):
    if url:
        page.goto(BASE + url)
    if wait_for:
        page.wait_for_selector(wait_for, timeout=10000)
    page.wait_for_timeout(400)
    page.screenshot(path=str(SHOTS / f"{name}-desktop.png"), full_page=True)
    HTML.joinpath(f"{name}.html").write_text(page.content())
    if mobile_too:
        page.set_viewport_size(MOBILE)
        page.wait_for_timeout(300)
        page.screenshot(path=str(SHOTS / f"{name}-mobile.png"), full_page=True)
        page.set_viewport_size(DESKTOP)
    print("captured", name)


def log_in(page, username):
    page.goto(BASE + "/accounts/login/")
    page.fill("#id_username", username)
    page.fill("#id_password", DEMO["password"])
    page.click("main button[type=submit]")
    page.wait_for_load_state("networkidle")


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    context = browser.new_context(viewport=DESKTOP, reduced_motion="reduce", locale="en-GB",
                                  timezone_id="Europe/London")
    page = context.new_page()
    slug = DEMO["slug"]

    # Visitor pages
    capture(page, "home", "/", mobile_too=True)
    capture(page, "home-postcode-check", "/?postcode=EC1A+1BB#areas")
    capture(page, "prices", "/prices/", mobile_too=True)
    capture(page, "instructor-profile", f"/instructors/{slug}/", mobile_too=True)
    capture(page, "how-it-works", "/about/")
    capture(page, "register", "/accounts/register/")
    page.click("main button[type=submit]")
    capture(page, "register-validation-errors")
    capture(page, "login", "/accounts/login/")
    capture(page, "error-404", "/this-page-does-not-exist/")

    # Learner pages
    log_in(page, "jamil")
    capture(page, "learner-dashboard", "/bookings/", mobile_too=True)
    capture(page, "booking-form", f"/bookings/new/{slug}/?date={DEMO['free_date']}", mobile_too=True,
            wait_for=".slot-button")
    page.click(".slot-button >> nth=2")
    page.fill("#id_pickup_postcode", "IG3 8XX")
    page.click("main button[type=submit]")
    capture(page, "booking-postcode-outside-area")
    capture(page, "checkout", f"/payments/booking/{DEMO['pending']}/", mobile_too=True)
    capture(page, "booking-detail", f"/bookings/{DEMO['next']}/")
    capture(page, "booking-cancel-confirm", f"/bookings/{DEMO['next']}/cancel/")
    capture(page, "progress", "/progress/", mobile_too=True)
    capture(page, "my-details", "/accounts/profile/")
    capture(page, "prices-logged-in", "/prices/")
    capture(page, "learner-blocked-from-diary", "/bookings/diary/")

    # Instructor pages
    context.clear_cookies()
    log_in(page, "ali")
    capture(page, "instructor-diary", "/bookings/diary/", mobile_too=True)
    capture(page, "instructor-sign-off", f"/bookings/{DEMO['sign_off']}/complete/")
    capture(page, "instructor-rate-skills", "/progress/learners/jamil/")
    capture(page, "instructor-edit-profile", "/instructors/me/edit/")

    browser.close()
