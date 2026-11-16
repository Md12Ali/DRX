"""
Take screenshots of every page and save each page's HTML for validation.
Also, on every page: run the axe-core accessibility checker (WCAG 2.1 A and AA),
record any JavaScript console errors, and collect internal links to check
for broken ones at the end.
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

AXE = pathlib.Path("node_modules/axe-core/axe.min.js").read_text()
REPORT = pathlib.Path("docs/testing")
axe_results = {}
console_errors = []
internal_links = set()

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
    check_accessibility(page, name)
    for href in page.eval_on_selector_all("a[href^='/']", "links => links.map(a => a.getAttribute('href'))"):
        internal_links.add(href.split("#")[0])
    if mobile_too:
        page.set_viewport_size(MOBILE)
        page.wait_for_timeout(300)
        page.screenshot(path=str(SHOTS / f"{name}-mobile.png"), full_page=True)
        page.set_viewport_size(DESKTOP)
    print("captured", name)


def check_accessibility(page, name):
    """Run axe-core on the page and keep any WCAG 2.1 A/AA violations."""
    page.add_script_tag(content=AXE)
    result = page.evaluate(
        "async () => (await axe.run(document, {runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']}))"
        ".violations.map(v => ({id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length}))"
    )
    axe_results[name] = result


def write_reports(page):
    """Accessibility, console and broken-link reports for docs/testing/."""
    lines = []
    total = 0
    for name, violations in axe_results.items():
        total += len(violations)
        status = "no violations" if not violations else f"{len(violations)} violation(s)"
        lines.append(f"{name}: {status}")
        for v in violations:
            lines.append(f"    [{v['impact']}] {v['id']}: {v['help']} ({v['nodes']} element(s))")
    lines.append("")
    lines.append(f"axe-core WCAG 2.1 A/AA: {len(axe_results)} pages checked, {total} violation(s) in total.")
    REPORT.joinpath("accessibility.txt").write_text("\n".join(lines) + "\n")

    REPORT.joinpath("console-errors.txt").write_text(
        ("\n".join(console_errors) if console_errors else "No JavaScript errors in the console on any page.") + "\n"
    )

    broken = []
    for href in sorted(internal_links):
        if not href or href.startswith("/admin") or "logout" in href:
            continue
        status = page.request.get(BASE + href, max_redirects=5).status
        if status >= 400 and status != 403:
            broken.append(f"{status} {href}")
    REPORT.joinpath("link-check.txt").write_text(
        f"{len(internal_links)} internal links checked.\n"
        + ("\n".join(broken) if broken else "No broken internal links.") + "\n"
    )


def record_console(page, msg):
    """Keep console errors, except the expected 403/404 on the two error pages we visit on purpose."""
    expected = "Failed to load resource" in msg.text and (
        "this-page-does-not-exist" in page.url or "/bookings/diary/" in page.url
    )
    if msg.type == "error" and not expected:
        console_errors.append(f"{page.url}: {msg.text}")


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
    page.on("console", lambda msg: record_console(page, msg))
    page.on("pageerror", lambda error: console_errors.append(f"{page.url}: {error}"))
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

    write_reports(page)
    browser.close()
