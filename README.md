# DRX: driving lessons in East London

DRX is my personal driving-instructor website, built as a full-stack Django app. Learners can:
- check I cover their postcode
- book a lesson in a live time slot
- **buy money-saving lesson packages**
- pay online by card (Stripe) or with their package hours
- reschedule or cancel online
- watch their **test-ready score** rise as I rate their skills after each lesson

I get a diary, sign off lessons with notes, and record each learner's progress.

| | |
|---|---|
| Pay as you go | **£35 an hour** (1, 1.5 or 2-hour lessons) |
| Packages | 5 h £170 · 10 h £330 · 20 h £640 · 30 h £930 (editable in the admin) |
| Areas covered | **E1, E2, E3, E8, E9, E14, EC1, EC2, N1** |

The site is built around one instructor today. The data model still supports more instructors,
so DRX can grow into a school with branches later.

![DRX home page](docs/screenshots/home-desktop.png)

**Live site:** https://drx-hec8.onrender.com (free Render plan: the first visit after a quiet spell takes up to a minute to wake up)
[![Tests, validation and screenshots](https://github.com/Md12Ali/DRX/actions/workflows/ci.yml/badge.svg)](https://github.com/Md12Ali/DRX/actions/workflows/ci.yml)
**Repository:** https://github.com/Md12Ali/DRX

### For the assessor

- **Try it as a learner:** open the live site, choose *Book a lesson*, register (use a covered
  postcode such as `E3 5AA`), then pick a time. Card payments use Stripe **test mode**: card
  `4242 4242 4242 4242`, any future date, any CVC. No real money is taken.
- **Instructor and admin views:** login details are supplied with the submission, not in this
  repository.
- **Evidence:** tests, coverage, linting and W3C results are in [`docs/testing/`](docs/testing/),
  screenshots in [`docs/screenshots/`](docs/screenshots/), wireframes in
  [`docs/wireframes/`](docs/wireframes/), and a criterion-by-criterion map in
  [`docs/assessment-checklist.md`](docs/assessment-checklist.md).

---

## Contents

1. [Purpose and rationale](#purpose-and-rationale)
2. [User experience](#user-experience)
3. [Features](#features)
4. [Business rules](#business-rules)
5. [Data schema](#data-schema)
6. [Project structure](#project-structure)
7. [Technologies](#technologies)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Version control](#version-control)
11. [Security](#security)
12. [Credits](#credits)

---

## Purpose and rationale

I'm a trainee driving instructor working in East London. Most local instructors take bookings by phone
and WhatsApp, collect cash or bank transfers, and track progress on paper or in their head.
That causes double bookings, chasing payments, missed lessons, and learners who don't know how
close they are to being ready for the test.

DRX fixes this for three related audiences:

| Audience | Problem today | What DRX gives them |
|---|---|---|
| **Learner drivers** (17+, often students or shift workers) | Phone tag to find a slot; no idea how close they are to test standard | Live availability, instant booking, card payment, online rescheduling, a visible test-ready score |
| **Parents paying for lessons** | Unclear what they're paying for | Clear prices, receipts from Stripe, lesson notes |
| **Instructors** | Double bookings, unpaid lessons, paperwork | A diary that can't be double-booked, payment before the lesson, progress records in one place |

The progress tracker uses the five-step scale UK instructors use (Introduced, Under full
instruction, Prompted, Seldom prompted, Independent) across a 16-skill syllabus. It turns "how
many more lessons do I need?" into a number the learner can see.

---

## User experience

### User stories

**Visitor**
1. Understand what DRX offers and what lessons cost from the home page.
2. Check whether my postcode is covered before signing up.
3. Compare pay-as-you-go and package prices, and see how much each package saves.
4. See the instructor's qualification, car, working hours, reviews and free slots.

**Learner**
4. Register, log in and log out.
5. Save my phone number and pick-up address once, so I'm never asked again when booking.
6. Pick a date and see only the times that are actually free.
7. Choose a 1, 1.5 or 2-hour lesson and see the price update.
8. Pay securely by card and get clear confirmation, or a clear message if payment fails or I cancel.
8a. Buy a package of hours, see my balance, and pay for lessons with those hours.
8b. Get my hours back automatically if I cancel a lesson paid with package hours.
9. See my next lesson, upcoming lessons and past lessons.
10. Reschedule or cancel up to 24 hours before, and get a refund automatically.
11. Read my instructor's notes after each lesson.
12. See my progress in every skill and a test-ready percentage.
13. Review my instructor after a completed lesson, then edit or delete my review.
14. Delete my account and data.

**Instructor**
15. See my next 14 days of lessons in a diary.
16. Sign off lessons with notes.
17. Rate a learner's skills after a lesson.
18. Edit my public profile, prices, working days and hours.
19. Cancel a lesson (e.g. illness) and refund the learner automatically.

**Owner (admin)**
20. Add instructors, manage bookings, payments, reviews and the syllabus in the Django admin.

### Design

- **Look and feel:** a bright, friendly "fresh licence" theme, aimed at young learners rather than
  a corporate look. Warm paper background (`#fff8ef`) with deep indigo ink (`#1b1a3a`) for text,
  outlines and the footer. Cards, buttons and stickers have a 2px ink outline and a hard offset
  shadow, so they look like printed stickers; buttons "press in" when clicked.
- **Colours:** tangerine (`#ff6b3d`) for main actions, sunshine yellow (`#ffd23f`) for labels and
  the road markings, mint (`#7ee0b8`) for progress and the contact card, lilac (`#d9cdff`) for the
  areas section, L-plate red (`#d62839`) for warnings and destructive actions, green (`#0f7a55`)
  for success. Every text and background pair meets WCAG AA contrast: the tangerine and yellow
  are always paired with dark ink text, never white.
- **Type:** *Bricolage Grotesque* (bold, characterful) for headings and *DM Sans* for body text,
  both from Google Fonts.
- **Contact:** my phone number (07476 283894) appears in the header, the home page hero, a
  "Not sure yet? Just ask" card, the FAQ, the How it works page and the footer. It uses `tel:` and
  `sms:` links, so learners on a phone can call or text with one tap. The number is set once in
  `CONTACT_PHONE` in settings.
- **Layout:** layout patterns (hero with search, stats strip, steps, bento features, reviews, FAQ,
  call to action) follow the VibeUI layout library. Booking pages use a two-column layout with a
  sticky summary panel, which stacks on mobile.
- **Wireframes:** low-fidelity layouts for desktop and mobile were planned before building.
  They are in [`docs/wireframes/`](docs/wireframes/).

| Page | Wireframe |
|---|---|
| Home | [01-home.png](docs/wireframes/01-home.png) |
| Prices and packages | [02-prices.png](docs/wireframes/02-prices.png) |
| Book a lesson | [03-booking.png](docs/wireframes/03-booking.png) |
| Checkout | [04-checkout.png](docs/wireframes/04-checkout.png) |
| Learner dashboard | [05-learner-dashboard.png](docs/wireframes/05-learner-dashboard.png) |
| Progress | [06-progress.png](docs/wireframes/06-progress.png) |
| Instructor diary | [07-instructor-diary.png](docs/wireframes/07-instructor-diary.png) |
| Instructor profile | [08-instructor-profile.png](docs/wireframes/08-instructor-profile.png) |

![Home wireframe](docs/wireframes/01-home.png)

### Accessibility

- Semantic landmarks, one `h1` per page, skip link, visible amber focus ring.
- Every input has a label. Errors and help text are linked to fields (`aria-describedby`, `aria-invalid`).
- Time-slot buttons use `aria-pressed`. Availability and countdown updates use `aria-live`.
- The test-ready score uses a native `<progress>` element. Radio groups use `fieldset`/`legend`.
- Animations are disabled for users who prefer reduced motion.
- 44px minimum touch targets.

### UX decisions worth noting

- **Honest, positive instructor details.** Instead of a formal qualification badge, the home page
  and profile list five checkable selling points (calm and patient, lessons planned around you,
  clear progress, door-to-door pick-up, flexible lengths). A small line underneath still says I'm
  a DVSA-licensed trainee, because DVSA rules say a trainee must not appear to be a fully
  qualified instructor. When the `qualification` field is set to ADI, it reads
  "Approved Driving Instructor (ADI)" instead.
- **Progressive enhancement:** the slot picker loads free times with JavaScript, but the date and
  time inputs still work without it. The server checks every rule again, so a booking can never
  break them.
- **Confirmation pages** (not pop-ups) for learner cancellations, account deletion and review
  deletion. One exception: the instructor "Cancel and refund" button uses a browser `confirm()`
  so instructors can act quickly from the lesson page. The action is still POST-only and CSRF-protected.
- **Never ask twice:** the pick-up address is pre-filled from the learner's details, and Stripe
  checkout is pre-filled with their email.
- **Slot hold:** an unpaid booking holds its time for 35 minutes, with a visible countdown, so two
  learners can't pay for the same slot.
- **Inline styles:** none, except the CSS variable set by JavaScript for the dashboard score ring.

---

## Features

| Area | Features |
|---|---|
| Home | Personal hero, key facts, prices and packages, **postcode checker** (works with or without JavaScript), areas covered, about me, bento features, real reviews only, FAQ |
| Prices | Pay-as-you-go prices, every package with price per hour and saving, learner's hour balance and purchase history |
| Packages | Stripe Checkout for packages, success/cancel handling, webhook; hours spent on bookings and returned on cancellation |
| Areas | Pick-up postcodes checked against E1, E2, E3, E8, E9, E14, EC1, EC2, N1 on sign-up details and every booking |
| Instructor profile | "Why learn with me" highlights, facts, bio, prices, 14-day availability strip, reviews |
| Booking | Live slot picker (JSON API), 1/1.5/2-hour lessons, notes, rule checks, 35-minute payment hold |
| Payments | Stripe Checkout, success/cancel pages, webhook, automatic refunds on cancellation |
| Learner dashboard | Next lesson, test-ready ring, hours driven, upcoming and past lessons |
| Booking detail | Status, payment, lesson notes, reschedule/cancel (learner) or sign-off/cancel (instructor) |
| Progress | 16-skill syllabus, five-step levels, test-ready score, "focus next" suggestions |
| Instructor tools | 14-day diary, lessons to sign off, learner list, skill rating form, profile editor |
| Reviews | Only after a completed lesson; one per learner per instructor; full CRUD |
| Accounts | Register, log in, log out (POST), details with UK phone/postcode validation, delete account |
| Errors | Custom 403, 404 and 500 pages |

### CRUD summary

| Model | Create | Read | Update | Delete |
|---|---|---|---|---|
| Booking | Book a lesson | Dashboard, detail, diary | Reschedule; instructor sign-off | Cancel (status change and refund) |
| Review | Write a review | Instructor profile, home | Edit review | Delete review |
| Profile | Created on sign-up | My details | Edit details | Delete account |
| Instructor | Admin | Directory, profile | Instructor edits own profile | Admin |
| SkillRating | Instructor rates a skill | Progress pages | Re-rate | Set to "Not started" |
| Payment | Checkout | Booking detail, admin | Webhook, success, cancel, refund | Admin |
| LessonPackage | Data migration / admin | Prices page, home | Admin (prices, popular flag) | Admin (or deactivate) |
| PackagePurchase | Buy a package | Prices page history, admin | Webhook, success, cancel | Admin |

---

## Business rules

All rules live in one place: `drx/settings.py` (values) and `bookings/services.py` (logic).

| Rule | Value |
|---|---|
| Minimum notice | 12 hours |
| Book ahead | up to 8 weeks |
| Start times | on the hour or half hour, inside the instructor's working hours and days |
| Lesson fits | lesson must end by the instructor's finish time |
| No clashes | instructor and learner can't be double-booked (overlap check) |
| Payment hold | unpaid bookings hold the slot for 35 minutes, then expire |
| Change/cancel | learners can reschedule or cancel until 24 hours before; refund is automatic |
| Lesson length | locked once paid (cancel and rebook to change it) |
| Pick-up area | postcode district must be E1, E2, E3, E8, E9, E14, EC1, EC2 or N1 (EC1A counts as EC1, E1W as E1, N1C as N1) |
| Package hours | balance = paid package hours − hours of confirmed/completed lessons paid with hours, so cancelling returns hours automatically |
| Reviews | only after a completed lesson; one per learner per instructor |
| Ratings | only by an instructor who has a confirmed or completed lesson with that learner |
| Test-ready | at least 85% overall **and** every skill "Seldom prompted" or better |

---

## Data schema

PostgreSQL in production, SQLite locally, through Django's ORM. Seven apps, one per natural part of the domain.

```mermaid
erDiagram
    USER ||--|| PROFILE : "has"
    USER ||--o| INSTRUCTOR : "may be"
    USER ||--o{ BOOKING : "books (learner)"
    INSTRUCTOR ||--o{ BOOKING : "teaches"
    BOOKING ||--o| PAYMENT : "paid by card"
    USER ||--o{ PACKAGEPURCHASE : "buys"
    LESSONPACKAGE ||--o{ PACKAGEPURCHASE : "sold as"
    INSTRUCTOR ||--o{ REVIEW : "receives"
    USER ||--o{ REVIEW : "writes"
    USER ||--o{ SKILLRATING : "is rated"
    SKILL ||--o{ SKILLRATING : "rated in"
```

### `accounts.Profile`
| Field | Type | Notes |
|---|---|---|
| user | OneToOne → User | Created by a `post_save` signal |
| phone | Char(20) | UK mobile, regex validated |
| pickup_address | Char(200) | Pre-fills bookings |
| postcode | Char(10) | UK postcode, regex validated, stored upper-case |
| transmission | Choice | manual / automatic |
| created_on | DateTime | |

### `instructors.Instructor`
| Field | Type | Notes |
|---|---|---|
| user | OneToOne → User | `related_name="instructor"` |
| slug | Slug, unique | Used in URLs |
| display_name, tagline, bio | Char / Text | Public profile |
| qualification | Choice | trainee / adi. Trainees must not advertise as ADIs |
| areas_covered | Char(200) | Comma-separated; searchable |
| teaches | Choice | manual / automatic / both |
| car, photo | Char / Image | |
| hourly_rate_pence | PositiveInteger | £10–£200, stored in pence |
| working_days | Char(7) | e.g. `"012345"` = Mon–Sat |
| day_start, day_end | Time | Working hours |
| is_accepting_pupils | Boolean | Hides booking when false |

### `instructors.Review`
| Field | Type | Notes |
|---|---|---|
| instructor | FK → Instructor | |
| learner | FK → User | |
| rating | SmallInteger 1–5 | |
| comment | Text(600) | Minimum 10 characters |
| created_on / updated_on | DateTime | |

Constraint: `one_review_per_learner` (instructor, learner).

### `bookings.Booking`
| Field | Type | Notes |
|---|---|---|
| learner | FK → User | Cascade |
| instructor | FK → Instructor | **Protect**: can't delete an instructor with lessons |
| start / end | DateTime | `end` is set from the duration on save |
| pickup_postcode | Char(10) | Must be in a covered district |
| payment_method | Choice | card / package |
| duration_minutes | Choice | 60 / 90 / 120 |
| pickup_address | Char(200) | |
| learner_notes / instructor_notes | Text | |
| price_pence | PositiveInteger | Fixed at booking time |
| status | Choice | pending, confirmed, completed, cancelled, expired |
| created_on / updated_on | DateTime | `created_on` drives the payment hold |

Constraint: `booking_ends_after_start`.

### `payments.Payment`
| Field | Type | Notes |
|---|---|---|
| booking | OneToOne → Booking | |
| stripe_session_id | Char, unique | Checkout Session |
| stripe_payment_intent | Char | Needed for refunds |
| amount_pence | PositiveInteger | |
| status | Choice | pending, paid, failed, refunded, refund_failed |
| created_on / paid_on | DateTime | |

### `packages.LessonPackage`
| Field | Type | Notes |
|---|---|---|
| slug, name, description | Slug / Char | |
| hours | SmallInteger | e.g. 10 |
| price_pence | PositiveInteger | e.g. 33000 = £330 |
| is_popular, is_active, order | Boolean / Integer | Display options |

### `packages.PackagePurchase`
| Field | Type | Notes |
|---|---|---|
| learner → User, package → LessonPackage (protect) | FK | |
| hours, price_pence | Integer | Copied at purchase so later price changes don't affect it |
| status | Choice | pending, paid, failed |
| stripe_session_id (unique), stripe_payment_intent | Char | |
| created_on / paid_on | DateTime | |

### `progress.Skill` and `progress.SkillRating`
| Skill field | Notes |
|---|---|
| name (unique), category, description, order | 16 skills loaded by data migration `0002_seed_syllabus` |

| SkillRating field | Notes |
|---|---|
| learner → User, skill → Skill | unique together (`one_rating_per_skill`) |
| level | 1 Introduced … 5 Independent |
| updated_by → User | the instructor who set it |

---

## Project structure

```
drx/            settings (all config in one place), root URLs, WSGI/ASGI
core/           home, about, postcode checker, error handlers, postcode helpers, test factories, setup_instructor command
accounts/       Profile, registration, log in/out, learner details, context processor
instructors/    Instructor, Review, directory, profiles, availability API, reviews CRUD
bookings/       Booking, booking rules (services.py), booking/reschedule/cancel, diary, sign-off
payments/       Payment, shared Stripe client, card or package-hours payment, webhook, refunds
packages/       LessonPackage, PackagePurchase, hour balance, prices page, buying packages
progress/       Skill, SkillRating, syllabus data migration, progress pages, rating form
templates/      base.html, 403/404/500, shared includes
static/         css/style.css, js/script.js, images/
```

Each app has its own models, forms, views, namespaced URLs, admin, templates, migrations and tests.

---

## Technologies

Python 3.12 · Django 5.2 · PostgreSQL (Neon) · Stripe (Checkout, Webhooks, Refunds) · Pillow ·
WhiteNoise · Gunicorn · dj-database-url · HTML5 · CSS3 · vanilla JavaScript · Google Fonts
(Archivo, Inter) · Git and GitHub · GitHub Actions · Render · Playwright (screenshots) ·
W3C Nu validator · JSHint · flake8 · coverage.py

---

## Testing

All test evidence is produced automatically and committed to this repository, so it always
matches the current code:

| Evidence | Where |
|---|---|
| Automated test run (118 tests) | [`docs/testing/test-results.txt`](docs/testing/test-results.txt) |
| Code coverage | [`docs/testing/coverage.txt`](docs/testing/coverage.txt) |
| PEP 8 (flake8) | [`docs/testing/flake8.txt`](docs/testing/flake8.txt) |
| JavaScript (JSHint) | [`docs/testing/jshint.txt`](docs/testing/jshint.txt) |
| HTML (W3C Nu validator, every page) | [`docs/testing/html-validation.txt`](docs/testing/html-validation.txt) |
| CSS (W3C Nu validator) | [`docs/testing/css-validation.txt`](docs/testing/css-validation.txt) |
| Screenshots of every page | [`docs/screenshots/`](docs/screenshots) |

### How the testing is automated

1. **GitHub Actions** ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs on every push.
   It installs the project, checks the migrations, runs the tests with coverage, runs flake8 and
   JSHint, builds a demo database ([`scripts/ci_demo_data.py`](scripts/ci_demo_data.py)), starts
   the site, takes screenshots of every page with Playwright
   ([`scripts/ci_screenshots.py`](scripts/ci_screenshots.py)), and validates each page's HTML
   and the stylesheet with the W3C Nu validator. The results are committed back into `docs/`.
2. **Render** runs [`build.sh`](build.sh) on every deploy. It checks the migrations, runs all
   118 tests and Django's deployment checks *before* the new version can go live. A failing test
   blocks the deploy.

### Results

- **Automated tests:** 118 tests, all passing. During development the first real run found 3
  test mistakes (114/117), which were fixed in commit `56ad0fb`.
- **Coverage:** 90% of the application code.
- **flake8:** no issues (PEP 8, with Django's 119-character line length set in `setup.cfg`).
- **JSHint:** no warnings (`esversion: 11`).
- **W3C HTML:** no errors on all 23 pages checked (public, learner and instructor pages).
- **W3C CSS:** no errors in `static/css/style.css`.
- The first validator run found 3 HTML errors (empty `for` on radio labels, an `<img>` without
  `src`, an invalid `autocomplete` value). They were fixed in commit `6d8e46f`.

What the automated tests cover:
- **bookings:** every booking rule (notice, booking window, working hours, day off, half-hour
  starts, instructor and learner clashes, rescheduling), hold expiry, permissions, the change
  cut-off, cancelling with a refund or with package hours, instructor sign-off and cancellation.
- **payments:** checkout page, redirect to Stripe, Stripe outage, missing keys, expired hold,
  success checked with Stripe, unpaid sessions not trusted, cancel page, webhooks, refunds.
- **packages:** savings maths, hour balance, paying with hours (enough / not enough), buying
  through Stripe, success, cancel, webhook.
- **instructors:** pro-rata pricing, start-time generation, filters, availability API, profile
  editing rules, review permissions and CRUD.
- **progress:** syllabus data migration, score maths, test-ready rule, rating permissions.
- **accounts / core:** sign-up, unique email, UK phone and postcode validation, covered
  postcodes, anonymous-only pages, POST-only logout, account deletion, home, about and 404.

### Manual testing

Each step was run in a real browser (Chromium, desktop 1366px and mobile 390px) against the
app with demo data, and the screenshot was saved in `docs/screenshots/`. The steps are written so
they can be repeated on the live site.

| # | Test | Expected | Evidence |
|---|---|---|---|
| 1 | Open the home page | Hero, prices, packages, areas, FAQ | `home-desktop.png`, `home-mobile.png` |
| 2 | Check postcode EC1A 1BB | "Yes! … is in EC1" | `home-postcode-check-desktop.png` |
| 3 | Open Prices | Pay as you go plus 4 packages with savings | `prices-desktop.png` |
| 4 | Submit the empty sign-up form | Every required field shows an error | `register-validation-errors-desktop.png` |
| 5 | Log in as a learner | Dashboard: next lesson, score, hours | `learner-dashboard-desktop.png` |
| 6 | Pick a date when booking | Free start times appear | `booking-form-desktop.png` |
| 7 | Book with postcode IG3 8XX | "Sorry, pick-ups are only available in…" | `booking-postcode-outside-area-desktop.png` |
| 8 | Continue to payment | Summary, countdown, package or card option | `checkout-desktop.png` |
| 9 | Open a booking, then Cancel | Confirmation page before cancelling | `booking-cancel-confirm-desktop.png` |
| 10 | Open Progress | Score and every skill's level | `progress-desktop.png` |
| 11 | Learner opens `/bookings/diary/` | 403 "No entry" page | `learner-blocked-from-diary-desktop.png` |
| 12 | Log in as the instructor | Diary and lessons to sign off | `instructor-diary-desktop.png` |
| 13 | Sign off a lesson | Notes form | `instructor-sign-off-desktop.png` |
| 14 | Rate a learner's skills | Five-step rating per skill | `instructor-rate-skills-desktop.png` |
| 15 | Visit a missing page | Custom 404 with links home | `error-404-desktop.png` |
| 16 | Pay with Stripe test card 4242 4242 4242 4242 | "You're booked in!" | Needs Stripe test keys on Render |
| 17 | Mobile layout (390px) | Single column, collapsed menu | the `*-mobile.png` screenshots |
| 18 | Tap the phone number on a mobile | Phone app opens with 07476 283894 ready to call | `home-mobile.png` |

### Screenshots

| Home | Prices | Booking |
|---|---|---|
| ![Home](docs/screenshots/home-desktop.png) | ![Prices](docs/screenshots/prices-desktop.png) | ![Booking](docs/screenshots/booking-form-desktop.png) |
| **Checkout** | **Learner dashboard** | **Progress** |
| ![Checkout](docs/screenshots/checkout-desktop.png) | ![Dashboard](docs/screenshots/learner-dashboard-desktop.png) | ![Progress](docs/screenshots/progress-desktop.png) |
| **Instructor diary** | **Rate skills** | **Mobile** |
| ![Diary](docs/screenshots/instructor-diary-desktop.png) | ![Rate skills](docs/screenshots/instructor-rate-skills-desktop.png) | ![Mobile](docs/screenshots/home-mobile.png) |

### Known limitations

- Uploaded instructor photos are stored on the server's disk, which Render resets on each deploy.
  Use Cloudinary or S3 for photos in a long-term production setup. Without a photo, the site shows
  the instructor's initials.
- Times assume the UK time zone (`Europe/London`).

---

## Deployment

The live site runs on **Render** (web service, free plan). The database is **Neon**
(free PostgreSQL that doesn't expire).

### Run locally

```bash
git clone https://github.com/Md12Ali/DRX.git && cd DRX
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp env_example.py env.py        # then fill in your own keys
python manage.py migrate        # also loads the syllabus and the packages
python manage.py createsuperuser
python manage.py setup_instructor <your-username> --name "Mohammed Ali"
python manage.py runserver
python manage.py test           # 118 tests
```

### 1. Database on Neon

1. Sign up at neon.com (free, no card) and create a project, e.g. `drx`, in the EU (Frankfurt) region.
2. Copy the connection string. It looks like
   `postgresql://user:password@ep-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require`.
   **It contains a password, so never commit it.**

### 2. Web service on Render

1. Render → **New → Web Service** → connect the `Md12Ali/DRX` GitHub repository.
   (Or **New → Blueprint**, which reads [`render.yaml`](render.yaml).)
2. Settings: runtime **Python**, region **Frankfurt**, plan **Free**,
   build command `./build.sh`, start command `gunicorn drx.wsgi --log-file -`.
3. Environment variables:

   | Key | Value |
   |---|---|
   | `PYTHON_VERSION` | `3.12.8` |
   | `SECRET_KEY` | a long random string |
   | `DATABASE_URL` | the Neon connection string |
   | `SECURE_SSL_REDIRECT` | `True` |
   | `STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | from Stripe (test mode) |
   | `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD` | the admin account to create |
   | `INSTRUCTOR_NAME` | e.g. `Mohammed Ali` |

   `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are filled in automatically from Render's
   `RENDER_EXTERNAL_HOSTNAME`. `DEBUG` is **not** set, so it stays off.
4. Deploy. [`build.sh`](build.sh) installs the requirements, checks the migrations, **runs all
   the tests**, runs `check --deploy`, collects static files, migrates the Neon database, and
   creates the admin account and instructor profile.

### 3. Stripe

1. Stripe → Developers → API keys (test mode): put the keys in the Render environment variables.
2. Developers → Webhooks → add `https://drx-hec8.onrender.com/payments/webhook/` with the events
   `checkout.session.completed`, `checkout.session.expired`,
   `checkout.session.async_payment_succeeded` and `checkout.session.async_payment_failed`.
   Copy its signing secret into `STRIPE_WEBHOOK_SECRET`.
3. Test with card `4242 4242 4242 4242`, any future expiry date and any CVC.

### Checking the deployed version matches development

The same commit is tested three times: on your computer (`python manage.py test`), in GitHub
Actions, and in Render's build before it goes live. The live site's footer, prices and pages
match the screenshots taken from the development server in CI.

---

## Version control

- Git and GitHub from the start. Work is done on the `drx-website` branch and merged into `main`
  through a pull request, after the GitHub Actions checks pass.
- Commit messages describe one change each (for example `Fix W3C HTML errors: fieldset for
  radio groups…`), so the history shows how the app was built and fixed.
- `.gitignore` keeps out `env.py`, the local database, `staticfiles/`, media uploads and caches.

---

## Security

- No secrets in Git. Everything comes from environment variables, and `env.py` is git-ignored.
  The app refuses to start in production without `SECRET_KEY`.
- `DEBUG` is off by default. Secure cookies and an optional SSL redirect apply in production.
- CSRF on every form. Log out, cancel, sign-off and checkout use POST.
- Every booking, review and rating is checked on the server: learners only see their own bookings;
  instructors only see theirs; only staff reach `/admin/`.
- Payments are verified with Stripe on the server, never trusted from the URL. Webhooks are
  signature-checked. Card details never touch DRX.

---

## Credits

- Django, Stripe and WhiteNoise documentation.
- Syllabus and five-step progress scale based on common UK driver-training practice (DVSA).
- Layout patterns inspired by the VibeUI layout library. Fonts from Google Fonts.
- All content and code written for this project. Reviews on DRX only ever come from real learners
  who have completed a lesson.
- Postcode district names for the covered areas are approximate and for guidance.
