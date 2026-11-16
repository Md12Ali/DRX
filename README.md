<p align="center"><img src="docs/logo/drx-logo.png" alt="DRX logo" width="320"></p>

# DRX: automatic driving lessons in East London

[![Tests, validation and screenshots](https://github.com/Md12Ali/DRX/actions/workflows/ci.yml/badge.svg)](https://github.com/Md12Ali/DRX/actions/workflows/ci.yml)

DRX is my own driving-instructor website, built as a full-stack Django application. Learners check
that I cover their postcode, book a lesson in a live free slot, buy money-saving packages, pay online
with Stripe, reschedule or cancel online, and watch their **test-ready score** rise as I rate their
skills after each lesson. I get a diary, sign off lessons with notes and record each learner's progress.

Submitted for the Level 5 Diploma in Web Application Development, **Unit 4: Full Stack Frameworks
with Django**.

| | |
| --- | --- |
| Live site | <https://drx-hec8.onrender.com> (free Render plan: the first visit after a quiet spell can take up to a minute) |
| Repository | <https://github.com/Md12Ali/DRX> |
| Testing report | [TESTING.md](TESTING.md) |
| Criteria map | [docs/assessment-checklist.md](docs/assessment-checklist.md) |
| Author | Mohammed Ali ([Md12Ali](https://github.com/Md12Ali)) |

| Lessons | Price |
| --- | --- |
| Automatic, pay as you go | **£35 an hour** (1, 1.5 or 2-hour lessons) |
| Packages | 5 h £170 · 10 h £330 · 20 h £640 · 30 h £930 |
| Pick-up areas | **E1, E2, E3, E8, E9, E14, EC1, EC2, N1** |
| Contact | **07476 283894** (call or text) |

> **Payments use Stripe test mode.** Use card `4242 4242 4242 4242`, any future expiry date and any
> CVC. No real money is taken.

![DRX home page](docs/screenshots/home-desktop.png)

---

## Contents

1. [Project rationale and purpose](#1-project-rationale-and-purpose)
2. [User stories](#2-user-stories)
3. [UX and design](#3-ux-and-design)
4. [Features](#4-features)
5. [Business rules](#5-business-rules)
6. [Database schema](#6-database-schema)
7. [Security features](#7-security-features)
8. [Project structure](#8-project-structure)
9. [Running the project locally](#9-running-the-project-locally)
10. [Environment variables](#10-environment-variables)
11. [Testing](#11-testing)
12. [Deployment](#12-deployment)
13. [Development process](#13-development-process)
14. [Attribution and code ownership](#14-attribution-and-code-ownership)

---

## 1. Project rationale and purpose

I'm a DVSA-licensed trainee driving instructor teaching in an automatic car in East London. Most local
instructors take bookings by phone and WhatsApp, collect cash or bank transfers, and track progress on
paper or in their head. That causes double bookings, chasing payments, missed lessons, and learners who
don't know how close they are to being ready for the test.

DRX solves this for three related audiences:

| Audience | Problem today | What DRX gives them |
| --- | --- | --- |
| **Learner drivers** (17+, often students or shift workers) | Phone tag to find a slot; no idea how close they are to test standard | Live availability, instant booking, card payment, online rescheduling, a visible test-ready score |
| **Parents paying for lessons** | Unclear what they're paying for | Clear prices, Stripe receipts, lesson notes |
| **The instructor (me)** | Double bookings, unpaid lessons, paperwork | A diary that can't be double-booked, payment before the lesson, progress records in one place |

**Value.** Learners book in under a minute at any time of day, never pay for a slot someone else has,
get automatic refunds if they cancel in time, and save up to £120 with a package. The progress tracker
uses the five-step scale UK instructors use (Introduced, Under full instruction, Prompted, Seldom
prompted, Independent) across a 16-skill syllabus, which turns "how many more lessons do I need?" into
a number the learner can see.

**Why these choices.**
- **Django** gives authentication, forms with validation, an admin for me, and an ORM over a relational
  database, which suits data with many relationships (learners, lessons, payments, packages, skills).
- **Stripe Checkout** keeps card details off my server and handles 3-D Secure.
- **Render and Neon** host the site and a PostgreSQL database for free, without the database expiring.
- **Automatic only.** I teach in an automatic car, so learners default to automatic and the site says so.

---

## 2. User stories

Every story below is implemented and was checked in the manual tests in [TESTING.md](TESTING.md#5-manual-test-plan-and-results).

| # | As a | I want to | So that | Where it is met |
| --- | --- | --- | --- | --- |
| 1 | Visitor | understand what DRX offers and what lessons cost | I can decide quickly | Home page hero, prices, FAQ |
| 2 | Visitor | check whether my postcode is covered | I don't sign up for nothing | Home page postcode checker |
| 3 | Visitor | compare pay-as-you-go and package prices | I can choose the best value | Prices page with savings |
| 4 | Visitor | see the instructor's details, free slots and reviews | I can trust who I'm booking | Instructor profile |
| 5 | Visitor | call or text the instructor | I can ask questions before booking | Phone number in header, home page and footer |
| 6 | Learner | register, log in and log out | my bookings and progress are kept | Accounts app |
| 7 | Learner | save my phone and pick-up address once | I'm never asked again when booking | My details; booking form pre-filled |
| 8 | Learner | see a week timetable of when the instructor is free and booked, and book a free time straight from it | I can find a time that suits me | **Timetable** page, live slot picker |
| 9 | Learner | choose a 1, 1.5 or 2-hour lesson and see the price | I know what I'll pay | Booking form summary |
| 10 | Learner | pay securely and get a clear result | I know whether I'm booked | Stripe Checkout, success and cancel pages |
| 11 | Learner | buy a package, see my balance and pay with hours | I save money | Prices page, checkout "use package hours" |
| 12 | Learner | see my next, upcoming and past lessons | I can plan | Learner dashboard |
| 13 | Learner | reschedule or cancel up to 24 hours before | I'm refunded automatically | Booking detail |
| 14 | Learner | read notes after each lesson | I know what to practise | Booking detail |
| 15 | Learner | see my level in every skill and a test-ready score | I know how close I am | Progress page |
| 16 | Learner | review my instructor after a lesson, then edit or delete it | I can share my experience | Reviews |
| 17 | Learner | delete my account | my data is removed | My details |
| 18 | Instructor | see my lessons for the next 14 days | I can plan my week | Diary |
| 19 | Instructor | sign off lessons with notes | the learner knows what to work on | Sign-off page |
| 20 | Instructor | rate a learner's skills | their score stays up to date | Rate skills page |
| 21 | Instructor | edit my profile, working days and hours | the site matches my availability | Edit profile |
| 22 | Instructor | cancel a lesson and refund the learner | I can handle illness or breakdowns | Booking detail |
| 23 | Owner | manage everything in one place | I can fix mistakes | Django admin (staff only) |

---

## 3. UX and design

### Design principles

- **Purpose obvious in five seconds.** The hero says who, what, where and how much: "Learn to drive
  with Mohammed. Book online in 60 seconds." with £35/hour and a *Book a lesson* button.
- **One main action per screen.** The tangerine button always moves the learner forward (book, pay,
  continue). Secondary actions are white outlined buttons.
- **Immediate feedback.** Every create, update and delete shows a message. Free times load without a
  page reload; a countdown shows how long the slot is held during payment.
- **Never ask twice.** Pick-up address and postcode are pre-filled from the learner's details, and
  Stripe Checkout is pre-filled with their email.
- **See it, then book it.** The timetable works like a familiar diary: green means free, striped
  grey means booked, yellow means your own lesson. One tap on a free time opens the booking form with
  everything filled in, so booking takes two steps.
- **Mobile first.** Every layout stacks to one column on a phone; the phone number is tap-to-call.
- **Progressive enhancement.** Every form works without JavaScript; the server checks every rule again.

### Logo

![DRX logo](docs/logo/drx-logo.png)

The logo is original, drawn by hand as SVG for this project ([`static/images/logo.svg`](static/images/logo.svg)).
A steering wheel inside a tangerine badge says "driving" at any size, including the 16 px browser tab
icon. The yellow hub picks up the road-marking colour. The "DRX" letters are drawn as thick rounded
strokes so they match the badge, with the **X** in tangerine. A white version
([`logo-light.svg`](static/images/logo-light.svg)) is used on the dark footer, and the badge alone is
the favicon ([`favicon.svg`](static/images/favicon.svg)).

### Colour palette

A bright, friendly "fresh licence" theme aimed at young learners. Cards, buttons and stickers have a
2 px ink outline and a hard offset shadow, so they look like printed stickers; buttons press in when
clicked. Contrast ratios were calculated with the WCAG 2.1 formula and confirmed in the browser by
axe-core on every page ([TESTING.md](TESTING.md#4-accessibility-console-and-link-checks)).

| Role | Hex | Used for | Contrast |
| --- | --- | --- | --- |
| Ink (deep indigo) | `#1b1a3a` | Text, outlines, shadows, footer | 15.87:1 on Paper |
| Paper (warm cream) | `#fff8ef` | Page background | - |
| Tangerine | `#ff6b3d` | Main buttons, key facts ribbon, logo | Ink text on Tangerine 5.91:1 |
| Sunshine | `#ffd23f` | Labels, road markings, footer links | Ink on Sunshine 11.58:1; Sunshine on Ink 11.58:1 |
| Mint | `#7ee0b8` | Progress, contact card, ticks | Ink on Mint 10.55:1 |
| Lilac | `#d9cdff` | Areas section | Ink on Lilac 11.25:1; Ink-soft on Lilac 7.26:1 |
| Ink-soft / Muted | `#3b3a5c` / `#5d5c78` | Body and secondary text | 10.24:1 / 6.10:1 on Paper |
| Link | `#3b4cca` | Text links | 6.48:1 on Paper |
| Danger / Success | `#d62839` / `#0f7a55` | Delete buttons, errors / confirmed status | White on Danger 4.97:1; Success on its tint 4.65:1 |

Tangerine and yellow are always paired with dark ink text, never white. The keyboard focus ring is ink
on light backgrounds (15.87:1) and yellow on the dark footer (11.58:1), above the 3:1 minimum.
Statuses are never shown by colour alone: every badge has a text label.

### Typography

| Use | Typeface | Weight | Why |
| --- | --- | --- | --- |
| Headings, prices, numbers | Bricolage Grotesque | 700 to 800 | Bold and characterful; makes the brand feel friendly, not corporate |
| Body, forms, tables | DM Sans | 400 to 700 | Very legible on screens at small sizes |
| Fallback | System UI stack | - | The site stays fully usable if web fonts fail to load |

### Wireframes

Low-fidelity layouts for desktop and mobile were planned before building. They are in
[`docs/wireframes/`](docs/wireframes/).

| Page | Wireframe |
| --- | --- |
| Home | [01-home.png](docs/wireframes/01-home.png) |
| Prices and packages | [02-prices.png](docs/wireframes/02-prices.png) |
| Book a lesson | [03-booking.png](docs/wireframes/03-booking.png) |
| Checkout | [04-checkout.png](docs/wireframes/04-checkout.png) |
| Learner dashboard | [05-learner-dashboard.png](docs/wireframes/05-learner-dashboard.png) |
| Progress | [06-progress.png](docs/wireframes/06-progress.png) |
| Instructor diary | [07-instructor-diary.png](docs/wireframes/07-instructor-diary.png) |
| Instructor profile | [08-instructor-profile.png](docs/wireframes/08-instructor-profile.png) |
| Timetable | [09-timetable.png](docs/wireframes/09-timetable.png) |

![Home wireframe](docs/wireframes/01-home.png)

### Screenshots of the finished site

All screenshots are taken automatically by a real browser on every push (desktop 1366 px and mobile
390 px) and saved in [`docs/screenshots/`](docs/screenshots/).

| Home | Prices | Booking |
| --- | --- | --- |
| ![Home](docs/screenshots/home-desktop.png) | ![Prices](docs/screenshots/prices-desktop.png) | ![Booking](docs/screenshots/booking-form-desktop.png) |
| **Checkout** | **Learner dashboard** | **Progress** |
| ![Checkout](docs/screenshots/checkout-desktop.png) | ![Dashboard](docs/screenshots/learner-dashboard-desktop.png) | ![Progress](docs/screenshots/progress-desktop.png) |
| **Timetable** | **Instructor diary** | **Mobile timetable** |
| ![Timetable](docs/screenshots/timetable-desktop.png) | ![Diary](docs/screenshots/instructor-diary-desktop.png) | ![Mobile timetable](docs/screenshots/timetable-mobile.png) |

### Accessibility

- Semantic landmarks (`header`, `nav`, `main`, `footer`), one `h1` per page, a skip link.
- Every input has a label; errors and help text are linked to their field (`aria-describedby`,
  `aria-invalid`). Radio groups use `fieldset` and `legend`.
- Time-slot buttons use `aria-pressed`; availability and the payment countdown use `aria-live`.
- The test-ready score uses a native `<progress>` element.
- Animations are turned off for users who prefer reduced motion; touch targets are at least 44 px.
- External links open in a new tab and say so to screen readers.
- axe-core finds no WCAG 2.1 A or AA violations on any page checked.

### Design decisions that break a convention

- **Instructor cancel uses a browser `confirm()`.** Learner cancellations, account deletion and review
  deletion use full confirmation pages. The instructor's "Cancel and refund" button uses a quick
  `confirm()` so I can act fast from the lesson page. It is still POST-only and CSRF-protected.
- **One inline style.** The dashboard score ring sets one CSS variable from the template; everything
  else is in `style.css`.
- **Trainee note kept small.** The instructor profile shows positive highlights instead of a
  qualification badge, with a short line saying I'm a DVSA-licensed trainee. DVSA rules say a trainee
  must not appear to be a fully qualified instructor, so the line stays. When the `qualification` field
  is set to ADI, it reads "Approved Driving Instructor (ADI)" instead.

---

## 4. Features

| Area | Features |
| --- | --- |
| Home | Hero with price sticker, key facts ribbon, prices and packages, **postcode checker** (JSON, works without JavaScript too), areas covered, about me with highlights, features, real reviews only, FAQ, contact card |
| Contact | Phone 07476 283894 in the header, hero, FAQ, contact card and footer, with `tel:` and `sms:` links |
| Prices | Pay-as-you-go prices, every package with price per hour and saving, the learner's hour balance and purchase history |
| Packages | Stripe Checkout for packages, success and cancel handling, webhook; hours spent on bookings and returned on cancellation |
| Instructor profile | "Why learn with me" highlights, facts, bio, prices, 14-day availability strip, reviews |
| Timetable | Week grid (Monday to Sunday, half-hour rows) showing **free**, **booked** and **your lesson** slots for 1, 1.5 or 2-hour lessons, up to 8 weeks ahead; tap a free time to book it with the date, time and length filled in; learners never see who else booked, the instructor sees first names; day-by-day list on phones |
| Booking | Live slot picker (JSON API), 1/1.5/2-hour lessons, notes, rule checks, 35-minute payment hold with countdown |
| Payments | Stripe Checkout, success and cancel pages, webhook, automatic refunds on cancellation |
| Learner dashboard | Next lesson, test-ready ring, hours left, upcoming and past lessons |
| Booking detail | Status, payment, lesson notes, reschedule or cancel (learner), sign off or cancel (instructor) |
| Progress | 16-skill syllabus, five-step levels, test-ready score, "focus next" suggestions |
| Instructor tools | 14-day diary, lessons to sign off, learner list, skill rating form, profile editor |
| Reviews | Only after a completed lesson; one per learner per instructor; full CRUD |
| Accounts | Register, log in, log out (POST), details with UK phone and postcode validation, delete account |
| Errors | Custom 403, 404 and 500 pages with links back to the home page |

### CRUD summary

| Model | Create | Read | Update | Delete |
| --- | --- | --- | --- | --- |
| Booking | Book a lesson | Dashboard, detail, diary | Reschedule; instructor sign-off | Cancel (status change and refund) |
| Review | Write a review | Instructor profile, home | Edit review | Delete review |
| Profile | Created on sign-up | My details | Edit details | Delete account |
| Instructor | Admin / `setup_instructor` command | Profile | Instructor edits own profile | Admin |
| SkillRating | Instructor rates a skill | Progress pages | Re-rate | Set back to "Not started" |
| Payment | Checkout | Booking detail, admin | Webhook, success, cancel, refund | Admin |
| LessonPackage | Data migration / admin | Prices page, home | Admin (prices, popular flag) | Admin (or deactivate) |
| PackagePurchase | Buy a package | Prices page history, admin | Webhook, success, cancel | Admin |

Every change shows straight away in the interface, with a message confirming what happened.

### Defensive design

- All input is validated on the server by Django forms and model validators, whatever the browser
  sends: UK phone and postcode formats, covered postcode districts, lesson lengths, rating ranges,
  review length, prices between £10 and £200 an hour.
- Every booking rule is checked again on the server at the moment of booking, so a stale page or a
  hand-made request can't create a clash or a booking outside working hours.
- A database constraint (`booking_ends_after_start`) and unique constraints (one review per learner,
  one rating per skill) protect the data even if code is wrong.
- Payments are confirmed with Stripe on the server, never trusted from the URL. Webhooks are
  signature-checked. If Stripe is down or the keys are missing, the learner sees a clear message and
  is not charged. A refund that fails is flagged as "needs manual action" instead of being lost.
- Views that change data accept POST only; learners can only see and change their own bookings,
  reviews and details (others get 404 or 403).

---

## 5. Business rules

All values live in one place, `drx/settings.py`; the logic lives in `bookings/services.py`.

| Rule | Value |
| --- | --- |
| Minimum notice | 12 hours |
| Book ahead | up to 8 weeks |
| Start times | on the hour or half hour, inside the instructor's working days and hours |
| Lesson fits | the lesson must end by the instructor's finish time |
| No clashes | neither the instructor nor the learner can be double-booked |
| Payment hold | an unpaid booking holds its slot for 35 minutes, then expires |
| Change or cancel | learners can reschedule or cancel until 24 hours before; refunds are automatic |
| Lesson length | locked once paid (cancel and rebook to change it) |
| Pick-up area | postcode district must be E1, E2, E3, E8, E9, E14, EC1, EC2 or N1 (EC1A counts as EC1, E1W as E1, N1C as N1) |
| Package hours | balance = paid package hours − hours of confirmed or completed lessons paid with hours, so cancelling returns hours automatically |
| Reviews | only after a completed lesson; one per learner per instructor |
| Ratings | only by an instructor who has a confirmed or completed lesson with that learner |
| Test-ready | at least 85% overall **and** every skill at "Seldom prompted" or better |

---

## 6. Database schema

The project uses Django's ORM over a relational database: **PostgreSQL** in production (Neon) and
SQLite for quick local development. The database is configured in one place, the `DATABASE_URL`
environment variable read in `drx/settings.py`, so it can be changed without touching code.

There are **9 custom models in 6 apps**, plus Django's built-in `User`. Each app holds one set of
closely connected models. Data used by several apps is shared, not copied: bookings, payments,
packages and ratings all point at the same `User` and `Instructor` rows, and prices come from one
setting.

### Entity relationship diagram

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
    USER |o--o{ SKILLRATING : "updated by"
```

### Relationships and deletion behaviour

| From | Type | To | Field | On delete | What happens and why |
| --- | --- | --- | --- | --- | --- |
| Profile | One-to-one | User | `user` | CASCADE | Every account has exactly one profile, created by a `post_save` signal, and deleted with it. |
| Instructor | One-to-one | User | `user` | CASCADE | An instructor is a user with a public profile. |
| Booking | Many-to-one | User | `learner` | CASCADE | Deleting an account removes the learner's bookings ("delete my data"). |
| Booking | Many-to-one | Instructor | `instructor` | **PROTECT** | An instructor with lessons can't be deleted by mistake. |
| Payment | One-to-one | Booking | `booking` | CASCADE | A card payment belongs to exactly one booking. |
| PackagePurchase | Many-to-one | User | `learner` | CASCADE | Purchases go with the account. |
| PackagePurchase | Many-to-one | LessonPackage | `package` | **PROTECT** | A package that has been sold can't be deleted; it can be deactivated. Hours and price are copied onto the purchase so later price changes don't affect it. |
| Review | Many-to-one | Instructor | `instructor` | CASCADE | Reviews go with the instructor. |
| Review | Many-to-one | User | `learner` | CASCADE | Reviews go with the learner's account. |
| SkillRating | Many-to-one | User | `learner` | CASCADE | Ratings go with the learner. |
| SkillRating | Many-to-one | Skill | `skill` | CASCADE | Ratings go with the skill. |
| SkillRating | Many-to-one | User | `updated_by` | **SET NULL** | The rating survives if the instructor's account is removed. |

### Field tables

"Constraint" means the database enforces it; "Validation" means Django forms and validators check it
before saving.

#### accounts.Profile

| Field | Type | Rules |
| --- | --- | --- |
| user | OneToOne → User | CASCADE, `related_name="profile"` |
| phone | CharField(20), optional | Validation: UK mobile format |
| pickup_address | CharField(200), optional | Pre-fills bookings |
| postcode | CharField(10), optional | Validation: UK postcode; stored upper-case |
| transmission | CharField(10), choices manual / automatic | Default **automatic** |
| created_on | DateTimeField | Set automatically |

#### instructors.Instructor

| Field | Type | Rules |
| --- | --- | --- |
| user | OneToOne → User | CASCADE, `related_name="instructor"` |
| slug | SlugField(60) | Constraint: unique; used in URLs |
| display_name | CharField(60) | Required |
| tagline | CharField(120), optional | Shown on the home page |
| qualification | CharField(10), choices trainee / adi | Default trainee |
| bio | TextField(1200), optional | |
| areas_covered | CharField(200) | Comma-separated, searchable |
| teaches | CharField(10), choices manual / automatic / both | Default **automatic** |
| car | CharField(80), optional | |
| photo | ImageField, optional | Validation: image file |
| hourly_rate_pence | PositiveIntegerField | Validation: 1000 to 20000 (£10 to £200); default 3500 |
| working_days | CharField(7) | e.g. `"012345"` = Monday to Saturday |
| day_start / day_end | TimeField | Default 08:00 / 20:00 |
| is_accepting_pupils | BooleanField | Hides booking when false |
| created_on | DateTimeField | Set automatically |

#### instructors.Review

| Field | Type | Rules |
| --- | --- | --- |
| instructor | ForeignKey → Instructor | CASCADE |
| learner | ForeignKey → User | CASCADE |
| rating | PositiveSmallIntegerField | Validation: 1 to 5 |
| comment | TextField(600) | Validation: at least 10 characters |
| created_on / updated_on | DateTimeField | Set automatically |

Constraint: `one_review_per_learner` (instructor, learner) is unique.

#### bookings.Booking

| Field | Type | Rules |
| --- | --- | --- |
| learner | ForeignKey → User | CASCADE |
| instructor | ForeignKey → Instructor | PROTECT |
| start / end | DateTimeField | `end` is worked out from the duration |
| duration_minutes | PositiveSmallIntegerField, choices 60 / 90 / 120 | Default 60 |
| pickup_address | CharField(200) | Required |
| pickup_postcode | CharField(10) | Validation: covered district |
| learner_notes | TextField(500), optional | |
| instructor_notes | TextField(1000), optional | Written at sign-off |
| price_pence | PositiveIntegerField | Fixed at booking time |
| status | CharField(10), choices pending / confirmed / completed / cancelled / expired | Default pending |
| payment_method | CharField(10), choices card / package | Default card |
| created_on / updated_on | DateTimeField | `created_on` drives the 35-minute hold |

Constraint: `booking_ends_after_start` (`end > start`).

#### payments.Payment

| Field | Type | Rules |
| --- | --- | --- |
| booking | OneToOne → Booking | CASCADE |
| stripe_session_id | CharField(255), optional | Constraint: unique |
| stripe_payment_intent | CharField(255), optional | Needed for refunds |
| amount_pence | PositiveIntegerField | |
| status | CharField(15), choices pending / paid / failed / refunded / refund_failed | Default pending |
| created_on / paid_on | DateTimeField | `paid_on` set when Stripe confirms |

#### packages.LessonPackage

| Field | Type | Rules |
| --- | --- | --- |
| slug | SlugField(40) | Constraint: unique |
| name | CharField(60) | e.g. "Confidence" |
| hours | PositiveSmallIntegerField | e.g. 10 |
| price_pence | PositiveIntegerField | e.g. 33000 = £330 |
| description | CharField(200), optional | |
| is_popular / is_active | BooleanField | Highlight / hide |
| order | PositiveSmallIntegerField | Display order |

The four packages are created by a data migration.

#### packages.PackagePurchase

| Field | Type | Rules |
| --- | --- | --- |
| learner | ForeignKey → User | CASCADE |
| package | ForeignKey → LessonPackage | PROTECT |
| hours / price_pence | PositiveSmallIntegerField / PositiveIntegerField | Copied from the package when bought |
| status | CharField(10), choices pending / paid / failed | Default pending |
| stripe_session_id | CharField(255), optional | Constraint: unique |
| stripe_payment_intent | CharField(255), optional | |
| created_on / paid_on | DateTimeField | |

#### progress.Skill

| Field | Type | Rules |
| --- | --- | --- |
| name | CharField(80) | Constraint: unique |
| category | CharField(12), choices controls / roads / manoeuvres / test | |
| description | CharField(200), optional | |
| order | PositiveSmallIntegerField | Display order |

The 16 skills are created by the data migration `0002_seed_syllabus`.

#### progress.SkillRating

| Field | Type | Rules |
| --- | --- | --- |
| learner | ForeignKey → User | CASCADE |
| skill | ForeignKey → Skill | CASCADE |
| level | PositiveSmallIntegerField, choices 1 Introduced … 5 Independent | Default 1 |
| updated_by | ForeignKey → User, optional | SET NULL; the instructor who set it |
| updated_on | DateTimeField | Set automatically |

Constraint: `one_rating_per_skill` (learner, skill) is unique.

---

## 7. Security features

- **No secrets in Git.** `SECRET_KEY`, `DATABASE_URL` and the Stripe keys come from environment
  variables; `env.py` and `.env` are git-ignored. The app refuses to start in production without a
  `SECRET_KEY`.
- **DEBUG is off** unless `DEBUG=True` is set; the live site never sets it.
- **HTTPS:** SSL redirect, HSTS, secure session and CSRF cookies in production. `python manage.py
  check --deploy` passes in every Render build.
- **CSRF protection** on every form; log out, cancel, sign-off and checkout are POST-only.
- **Log-in required** for booking, paying, progress, reviews and details. Log-in and registration
  pages are only for visitors (logged-in users are redirected).
- **Permissions:** learners only see and change their own bookings, reviews and details; only
  instructors reach the diary, sign-off and rating pages (others get a 403 page); only staff reach
  `/admin/`, so regular users can't reach the database except through the app.
- **Payments:** card details never touch DRX; payment status comes from Stripe on the server; webhooks
  are signature-checked.

---

## 8. Project structure

```
drx/            settings (all configuration in one place), root URLs, WSGI/ASGI
core/           home, how it works, postcode checker, error pages, postcode helpers, test factories,
                setup_instructor command
accounts/       Profile, registration, log in and out, learner details, context processor
instructors/    Instructor, Review, profiles, availability API, reviews CRUD
bookings/       Booking, booking rules (services.py), book/reschedule/cancel, diary, sign-off
payments/       Payment, shared Stripe client, card or package-hours payment, webhook, refunds
packages/       LessonPackage, PackagePurchase, hour balance, prices page, buying packages
progress/       Skill, SkillRating, syllabus data migration, progress pages, rating form
templates/      base.html, 403/404/500 pages, shared includes
static/         css/style.css, js/script.js, images/ (logo, favicon)
scripts/        CI only: demo data and browser checks (screenshots, accessibility, links)
docs/           screenshots, wireframes, testing reports, logo, assessment checklist
```

Each app has its own models, forms, views, namespaced URLs (`app:name`), admin, templates,
migrations and tests. HTML, CSS, JavaScript and Python are in separate files; the stylesheet is linked
in the `<head>` and the script at the end of the `<body>`.

---

## 9. Running the project locally

Requires Python 3.12 and Git.

```bash
git clone https://github.com/Md12Ali/DRX.git && cd DRX
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp env_example.py env.py        # then fill in your own values
python manage.py migrate        # creates the tables, the 16 skills and the 4 packages
python manage.py createsuperuser
python manage.py setup_instructor <your-username> --name "Mohammed Ali"
python manage.py runserver
python manage.py test           # 127 tests
```

Without `DATABASE_URL`, the project uses a local SQLite file. Without Stripe keys, everything works
except card payment, which shows a friendly "payments are not available" message.

---

## 10. Environment variables

| Key | Needed | Example / notes |
| --- | --- | --- |
| `SECRET_KEY` | Production | A long random string |
| `DEBUG` | No | `True` only on your own computer; leave unset in production |
| `DATABASE_URL` | Production | Neon connection string; unset = local SQLite |
| `ALLOWED_HOSTS` | Local | `localhost,127.0.0.1` (Render's host is added automatically) |
| `SECURE_SSL_REDIRECT` | Production | `True` |
| `STRIPE_PUBLIC_KEY` / `STRIPE_SECRET_KEY` | For payments | Stripe **test** keys (`pk_test_…`, `sk_test_…`) |
| `STRIPE_WEBHOOK_SECRET` | For payments | `whsec_…` from the Stripe webhook |
| `CONTACT_PHONE` | No | Defaults to `07476 283894` |
| `DJANGO_SUPERUSER_USERNAME` / `_EMAIL` / `_PASSWORD` | First deploy | Creates the admin and instructor account during the build |
| `INSTRUCTOR_NAME` | No | e.g. `Mohammed Ali` |
| `PYTHON_VERSION` | Render | `3.12.8` |

---

## 11. Testing

The full report, with every manual test and its result, the accessibility checks, the bugs found and
fixed, and the known limitations, is in **[TESTING.md](TESTING.md)**. In summary:

| Check | Tool | Result |
| --- | --- | --- |
| Automated tests | `python manage.py test` | **127 tests, all pass** |
| Coverage | coverage.py | 90% of application code |
| Python style (PEP 8) | flake8 | 0 findings |
| JavaScript | JSHint | 0 warnings |
| HTML | W3C Nu HTML Checker | 0 errors on every page |
| CSS | W3C Nu checker (CSS) | 0 errors |
| Accessibility | axe-core, WCAG 2.1 A and AA | 0 violations on every page |
| Console | Browser run on every page | No JavaScript errors |
| Internal links | Browser run, logged in as each user type | No broken links |
| Migrations match models | `makemigrations --check` | No changes |
| Deployment check | `check --deploy` | No issues |
| Responsive | Screenshots at 1366 px and 390 px | Every main page |

**How it runs.** GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs every
check above on every push and saves the reports in [`docs/testing/`](docs/testing/) and the
screenshots in [`docs/screenshots/`](docs/screenshots/). Render's build ([`build.sh`](build.sh))
runs all the tests and `check --deploy` again before a new version can go live, so a failing test
blocks the deploy.

---

## 12. Deployment

The live site runs on **Render** (web service, free plan, Frankfurt) with a **Neon** PostgreSQL
database (free plan, Frankfurt, does not expire).

### 12.1 Create the database on Neon

1. Sign up at neon.com (free, no card) and create a project named `drx` in the **AWS Europe Central
   (Frankfurt)** region, PostgreSQL 17.
2. Open **Connect**, choose the pooled connection and copy the connection string. It looks like
   `postgresql://user:password@ep-xxx-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require`.
   **It contains a password, so never commit it.** Keep `sslmode=require`.

### 12.2 Create the web service on Render

1. Render → **New → Web Service** → connect the `Md12Ali/DRX` GitHub repository, branch `main`.
   (Or **New → Blueprint**, which reads [`render.yaml`](render.yaml).)
2. Settings: runtime **Python**, region **Frankfurt**, plan **Free**, build command `./build.sh`,
   start command `gunicorn drx.wsgi --log-file -`.
3. Add the environment variables from [section 10](#10-environment-variables): at least
   `PYTHON_VERSION`, `SECRET_KEY`, `DATABASE_URL` (the Neon string), `SECURE_SSL_REDIRECT=True`, the
   three Stripe keys and the `DJANGO_SUPERUSER_*` values. Do **not** set `DEBUG`.
4. Deploy. [`build.sh`](build.sh) then:
   1. installs the requirements;
   2. checks the migrations match the models;
   3. runs all the tests (a failure stops the deploy);
   4. runs `check --deploy`;
   5. collects static files (served by WhiteNoise);
   6. migrates the Neon database (tables, the 16 skills, the 4 packages);
   7. creates the admin account and its instructor profile.

### 12.3 Connect Stripe

1. Stripe dashboard (test mode) → **Developers → API keys**: copy the publishable and secret keys into
   `STRIPE_PUBLIC_KEY` and `STRIPE_SECRET_KEY` on Render.
2. **Developers → Webhooks → Add endpoint**: `https://drx-hec8.onrender.com/payments/webhook/` with
   the events `checkout.session.completed`, `checkout.session.expired`,
   `checkout.session.async_payment_succeeded` and `checkout.session.async_payment_failed`. Copy the
   signing secret into `STRIPE_WEBHOOK_SECRET`.
3. Redeploy, then pay for a lesson with card `4242 4242 4242 4242`.

### 12.4 Checking the live site matches development

- The same commit is tested on my computer, in GitHub Actions and in Render's build.
- The `Procfile` and `requirements.txt` are kept for other hosts (for example Heroku); on Render,
  `build.sh` does the same work.
- After each deploy, open the live site and compare it with the latest screenshots in
  `docs/screenshots/`, then run the manual tests in [TESTING.md](TESTING.md#5-manual-test-plan-and-results).

---

## 13. Development process

- **Git and GitHub from the start**, with one commit per feature or fix and messages that say what
  changed and why (for example `Fix W3C HTML errors: fieldset for radio groups, preview img src,
  autocomplete value`). Run `git log --stat` to see each change.
- **Branches and pull requests.** Work happens on feature branches (`drx-website`, `redesign`,
  `highlights`, `logo-automatic`) and is merged into `main` after the GitHub Actions checks pass.
- **Tests with every app.** Each app was committed with its own tests; the 127 tests run on every
  push and in every deploy. For honesty: tests were usually written in the same or the next commit as
  the feature, rather than always before it.
- **Bugs found by the checks are fixed in their own commits** and listed in
  [TESTING.md](TESTING.md#6-bugs-found-and-fixed).
- **Settings for each environment** come from environment variables, so the same `settings.py` works
  locally (SQLite, DEBUG on), in CI and in production (PostgreSQL, HTTPS, DEBUG off).

---

## 14. Attribution and code ownership

### Project code

- Everything in `drx/`, `core/`, `accounts/`, `instructors/`, `bookings/`, `payments/`, `packages/`,
  `progress/`, `templates/`, `static/` and `scripts/` was written for this project.
- The logo, favicon and wireframes are original. All site text is original; reviews on the site only
  ever come from real learners who have completed a lesson. There are no stock photos.
- **Development tools.** An AI assistant (Claude, by Anthropic) was used to help write and review code,
  tests, design and documentation. Commits made with its help carry a `Co-Authored-By: Claude`
  trailer. I am responsible for the submitted work and can explain every part of it.

### External libraries and services

Used unmodified; not my own work.

| Library / service | Used for | Licence |
| --- | --- | --- |
| [Django](https://www.djangoproject.com/) 5.2 | Web framework, ORM, authentication, forms, admin, tests | BSD-3-Clause |
| [Stripe Python](https://github.com/stripe/stripe-python) and Stripe Checkout | Payments, webhooks, refunds | MIT |
| [gunicorn](https://gunicorn.org/) | Production web server | MIT |
| [WhiteNoise](https://whitenoise.readthedocs.io/) | Serving static files | MIT |
| [dj-database-url](https://github.com/jazzband/dj-database-url) | Reading `DATABASE_URL` | BSD-3-Clause |
| [psycopg2](https://www.psycopg.org/) | PostgreSQL driver | LGPL |
| [Pillow](https://python-pillow.org/) | Instructor photo uploads | MIT-CMU |
| [Google Fonts](https://fonts.google.com/): Bricolage Grotesque, DM Sans | Typography | SIL Open Font Licence |

Testing tools (not part of the live site): [W3C Nu HTML Checker](https://validator.github.io/validator/)
(MIT), [axe-core](https://github.com/dequelabs/axe-core) (MPL-2.0),
[Playwright](https://playwright.dev/python/) (Apache-2.0), [flake8](https://flake8.pycqa.org/) (MIT),
[JSHint](https://jshint.com/) (MIT), [coverage.py](https://coverage.readthedocs.io/) (Apache-2.0).

### Patterns adapted from documentation

- Stripe Checkout sessions, webhooks and refunds follow the
  [Stripe documentation](https://docs.stripe.com/payments/checkout); the code in `payments/` and
  `packages/` is my own.
- Production settings follow the Django
  [deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) and the
  Render guide for Django.
- The five-step progress scale and the syllabus follow common UK driver-training practice (DVSA).
- Layout patterns (hero, pricing, features, FAQ, call to action) were inspired by the VibeUI layout
  library; the design and code are my own.
