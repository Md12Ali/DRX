# DRX testing report

Back to the [README](README.md).

## Contents

1. [Summary](#1-summary)
2. [Automated tests](#2-automated-tests)
3. [Code validation](#3-code-validation)
4. [Accessibility, console and link checks](#4-accessibility-console-and-link-checks)
5. [Manual test plan and results](#5-manual-test-plan-and-results)
6. [Bugs found and fixed](#6-bugs-found-and-fixed)
7. [Known limitations](#7-known-limitations)

---

## 1. Summary

Every check below runs automatically in GitHub Actions on every push
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)). The reports it produces are saved in
[`docs/testing/`](docs/testing/), and the screenshots in [`docs/screenshots/`](docs/screenshots/), so
the evidence always matches the code. Render's build ([`build.sh`](build.sh)) runs the tests again
before every deploy, so a failing test stops a broken version going live.

| Check | Tool | Result | Report |
| --- | --- | --- | --- |
| Automated tests | Django test runner | **127 tests, all pass** | [test-results.txt](docs/testing/test-results.txt) |
| Coverage | coverage.py | 90% of application code | [coverage.txt](docs/testing/coverage.txt) |
| Python style (PEP 8) | flake8 (max line 119) | 0 findings | [flake8.txt](docs/testing/flake8.txt) |
| JavaScript | JSHint (`esversion: 11`) | 0 warnings | [jshint.txt](docs/testing/jshint.txt) |
| HTML | W3C Nu HTML Checker | 0 errors on every page | [html-validation.txt](docs/testing/html-validation.txt) |
| CSS | W3C Nu checker (CSS mode) | 0 errors | [css-validation.txt](docs/testing/css-validation.txt) |
| Accessibility | axe-core, WCAG 2.1 A and AA | 0 violations on every page | [accessibility.txt](docs/testing/accessibility.txt) |
| JavaScript errors | Console of a real browser on every page | None | [console-errors.txt](docs/testing/console-errors.txt) |
| Internal links | Every link on every page, as the user who sees it | None broken | [link-check.txt](docs/testing/link-check.txt) |
| Migrations | `makemigrations --check --dry-run` | Models and migrations match | CI log |
| Deployment settings | `check --deploy --fail-level ERROR` | No issues | Render build log |
| Responsive design | Screenshots at 1366 px and 390 px | All main pages | [docs/screenshots/](docs/screenshots/) |

Test environment: Python 3.12, Django 5.2, SQLite for the test database (the same code runs on
PostgreSQL in production), Chromium through Playwright, Ubuntu (GitHub Actions).

---

## 2. Automated tests

Run them with:

```bash
python manage.py test                 # all 127 tests
coverage run manage.py test && coverage report
```

| App | What is tested |
| --- | --- |
| **bookings** | Every booking rule: 12-hour notice, 8-week window, working days and hours, half-hour starts, instructor and learner clashes, rescheduling, the 35-minute hold and its expiry, the 24-hour change cut-off, cancelling with a card refund or with package hours returned, instructor sign-off and cancellation, permissions (learners only see their own bookings, only instructors reach the diary). **Timetable:** free, booked and "your lesson" slots; longer lessons closing slots before another lesson; days off; visitors can look and free times link to the booking form with date, time and length; learners never see other learners' names; the instructor does; weeks are kept inside the booking window; the booking form is pre-filled from the timetable. |
| **payments** | Checkout page, redirect to Stripe, Stripe outage and missing keys handled with a message, expired hold, success checked with Stripe (an unpaid session is not trusted), cancel page, webhook signature and events, refunds and failed refunds. |
| **packages** | Savings maths, hour balance, paying for a lesson with hours (enough and not enough), buying through Stripe, success, cancel, webhook. |
| **instructors** | Pro-rata pricing, start-time generation, default automatic and trainee, profile page and highlights, availability API, profile editing rules, review permissions and full review CRUD. |
| **progress** | Syllabus data migration (16 skills), score maths, test-ready rule, rating permissions. |
| **accounts / core** | Sign-up, unique email, UK phone and postcode validation, covered postcodes, log-in and registration only for visitors, POST-only log-out, account deletion, home page, postcode checker (page and JSON), how it works page, phone number on every page, custom 404. |

The full output of the last run is in [test-results.txt](docs/testing/test-results.txt), and the
coverage per file in [coverage.txt](docs/testing/coverage.txt).

---

## 3. Code validation

| Language | How it was checked | Result |
| --- | --- | --- |
| Python | `flake8` with Django's 119-character line length (`setup.cfg`) | 0 findings |
| JavaScript | `npx jshint static/js/script.js` | 0 warnings |
| HTML | The rendered HTML of every page (visitor, learner and instructor pages, error pages, the timetable) checked with the W3C Nu HTML Checker | 0 errors |
| CSS | `static/css/style.css` checked with the W3C Nu checker in CSS mode | 0 errors |

The HTML is checked as the browser receives it (after Django has filled in the templates), because
template files with `{% %}` tags can't be validated directly.

---

## 4. Accessibility, console and link checks

[`scripts/ci_screenshots.py`](scripts/ci_screenshots.py) opens every page in Chromium as a visitor,
as a learner and as the instructor. On each page it:

1. takes desktop (1366 px) and, for the main pages, mobile (390 px) screenshots;
2. runs **axe-core** with the WCAG 2.1 A and AA rules;
3. records any **JavaScript error** in the console;
4. follows every **internal link** on the page, logged in as the same user, and records any error.

Results: **0 accessibility violations, no console errors, no broken links.**

The first run found two real problems, which were fixed (bugs 8 and 9 below): grey text on the lilac
section was 4.32:1, just under the 4.5:1 minimum, and the tangerine keyboard focus ring was 2.68:1
against the cream background, under the 3:1 minimum for focus indicators.

Also checked:
- **Keyboard:** every link, button, radio button and timetable slot can be reached with Tab and used
  with Enter or Space; the focus ring is always visible.
- **Reduced motion:** with "reduce motion" switched on (the screenshots are taken this way), the road
  animation and button movement are turned off.
- **Colour is never the only signal:** free, booked and own slots in the timetable have text labels
  ("Booked", "Your lesson", and a hidden "Book Monday 23 November at 10:00" for screen readers).

---

## 5. Manual test plan and results

Each case was run in a real browser (Chromium, through the scripted run above) against the app with
demo data, and the screenshot in the last column shows the result. Payment with a real Stripe test
card can only be run once the Stripe test keys are added on Render (case 13).

| # | Feature | Steps | Expected result | Result | Evidence |
| --- | --- | --- | --- | --- | --- |
| 1 | Home page | Open `/` | Logo, hero with £35/hour, automatic lessons, prices, packages, areas, FAQ, contact card | Pass | `home-desktop.png`, `home-mobile.png` |
| 2 | Postcode check | Enter `EC1A 1BB`, press Check | "Yes! EC1A 1BB is in EC1 …" | Pass | `home-postcode-check-desktop.png` |
| 3 | Prices | Open Prices | Pay as you go plus 4 packages with price per hour and saving | Pass | `prices-desktop.png` |
| 4 | Instructor profile | Open About me | Highlights (automatic car first), facts, prices, 14-day strip, link to the timetable | Pass | `instructor-profile-desktop.png` |
| 5 | Timetable (visitor) | Open Timetable while logged out | Week grid of free and booked times, note that booking needs an account | Pass | `timetable-visitor-desktop.png` |
| 6 | Timetable (learner) | Log in, open Timetable, choose next week | Free (mint), Booked (grey, no names), Your lesson (yellow); day counts; week buttons | Pass | `timetable-desktop.png` |
| 7 | Timetable on a phone | Same at 390 px | Day-by-day cards with free times as large buttons | Pass | `timetable-mobile.png` |
| 8 | Book from the timetable | Tap a free time | Booking form opens with that date, time and length already chosen | Pass (automated test `test_booking_form_is_prefilled_from_the_timetable`) | `booking-form-desktop.png` |
| 9 | Sign-up validation | Submit the empty sign-up form | Every required field shows an error | Pass | `register-validation-errors-desktop.png` |
| 10 | Learner dashboard | Log in as a learner | Next lesson, test-ready score, package hours, upcoming and past lessons | Pass | `learner-dashboard-desktop.png` |
| 11 | Live free times | Pick a date on the booking form | Free start times load without a page reload | Pass | `booking-form-desktop.png` |
| 12 | Postcode outside the area | Book with postcode `IG3 8XX` | "Sorry, pick-ups are only available in …" and nothing is booked | Pass | `booking-postcode-outside-area-desktop.png` |
| 13 | Card payment | Continue to payment, pay with `4242 4242 4242 4242` | Stripe Checkout, then "You're booked in!" | **To run on the live site once the Stripe test keys are added** | - |
| 14 | Checkout page | Open checkout for an unpaid booking | Summary, hold countdown, pay by card or with package hours | Pass | `checkout-desktop.png` |
| 15 | Booking detail | Open a booked lesson | Status, payment, notes, reschedule and cancel | Pass | `booking-detail-desktop.png` |
| 16 | Cancel confirmation | Press Cancel | A confirmation page appears before anything changes | Pass | `booking-cancel-confirm-desktop.png` |
| 17 | Progress | Open Progress | Score, test-ready rule and every skill's level | Pass | `progress-desktop.png` |
| 18 | My details | Open My details | Phone, pick-up address, postcode, automatic preselected | Pass | `my-details-desktop.png` |
| 19 | Permissions | Learner opens `/bookings/diary/` | 403 "No entry" page with a way back | Pass | `learner-blocked-from-diary-desktop.png` |
| 20 | Instructor diary | Log in as the instructor | Diary and lessons to sign off | Pass | `instructor-diary-desktop.png` |
| 21 | Instructor timetable | Open Timetable as the instructor | Booked slots show the learner's first name | Pass | `instructor-timetable-desktop.png` |
| 22 | Sign off a lesson | Open a past lesson, Sign off | Notes form | Pass | `instructor-sign-off-desktop.png` |
| 23 | Rate skills | Open a learner's progress | Five-step rating for each skill | Pass | `instructor-rate-skills-desktop.png` |
| 24 | Edit profile | Open Edit profile | Profile form with qualification, hours and days | Pass | `instructor-edit-profile-desktop.png` |
| 25 | Missing page | Open `/this-page-does-not-exist/` | Custom 404 with links back home | Pass | `error-404-desktop.png` |
| 26 | Phone number | Tap the number on a phone | Phone app opens with 07476 283894 | Pass (link is `tel:+447476283894`, automated test) | `home-mobile.png` |
| 27 | Mobile layout | Every main page at 390 px | Single column, menu button, no sideways scrolling | Pass | `*-mobile.png` |
| 28 | Back and forward | Use the browser's back and forward buttons after booking and cancelling | No errors; forms that change data use POST, so nothing is sent twice | Pass | - |

---

## 6. Bugs found and fixed

| # | Found by | Problem | Fix |
| --- | --- | --- | --- |
| 1 | Render build | With `SECURE_SSL_REDIRECT=True`, about 60 tests got 301 redirects instead of pages | The redirect and HSTS are skipped while the tests run (`RUNNING_TESTS` in `settings.py`) |
| 2 | First test run | 3 of 117 tests failed: a name also appears in the footer, a form test missed the new `qualification` field, an apostrophe was HTML-escaped | Tests now check the view's context, send every field and match the escaped text |
| 3 | W3C HTML checker | Radio-button groups had a `<label for="">` pointing at nothing | Radio and checkbox groups now use `fieldset` and `legend` |
| 4 | W3C HTML checker | The photo preview `<img>` had no `src` | Given an empty `data:` source until a photo is chosen |
| 5 | W3C HTML checker | Invalid `autocomplete` value on the pick-up address | Changed to `address-line1` |
| 6 | Screenshot review | The package-hours number on the dashboard was invisible (same colour as its card) | CSS specificity fixed |
| 7 | Screenshot review | After the redesign, two progress-bar labels were hard to read | Label colour fixed |
| 8 | axe-core | Grey text on the lilac areas section was 4.32:1 (needs 4.5:1) | Darker text on that section (7.26:1) |
| 9 | Contrast calculation | Tangerine focus ring was 2.68:1 on cream (needs 3:1) | Ink focus ring (15.87:1), yellow on the dark footer (11.58:1) |
| 10 | Link check | Learner-only links reported as 404 when checked as the instructor | The checker now follows links as the user who sees them |
| 11 | Code review | `env_example.py` contained a commented-out line of code | Replaced with an explanatory comment |

---

## 7. Known limitations

- **Card payment on the live site** needs the Stripe test keys and webhook to be added on Render
  (README section 12.3). Until then, the site shows a friendly "payments are not available" message
  and nothing is charged; package hours still work.
- **Instructor photos** are saved on the server's disk, which Render clears on each deploy. Without a
  photo, the site shows initials. Cloud storage (for example Cloudinary or S3) would fix this.
- **Times use UK time** (`Europe/London`), which suits a London instructor.
- **Free Render plan:** the first visit after 15 minutes without traffic takes up to a minute while
  the server wakes up.
