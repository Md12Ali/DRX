# Unit 4 Full Stack Frameworks with Django: assessment checklist

Where each criterion in the qualification specification is met in the DRX project.

## Pass criteria

| Criterion | How DRX meets it | Evidence |
|---|---|---|
| 1.1 Design a full-stack app with a relational database and multiple apps | Seven apps, one per part of the domain: `accounts`, `instructors`, `bookings`, `payments`, `packages`, `progress`, `core` | README → Project structure, Data schema |
| 1.2 Front end meets accessibility guidelines and UX principles | Semantic landmarks, skip link, labels, `aria-*`, focus styles, reduced motion, responsive; 0 axe-core WCAG 2.1 AA violations | README → Accessibility; `docs/testing/accessibility.txt`; `docs/screenshots/*-mobile.png` |
| 1.3 Develop the app with Django, a relational DB, interactive front end, multiple apps | Django 5.2, PostgreSQL (Neon), weekly timetable, live slot picker, postcode checker | Live site; `static/js/script.js` |
| 1.4 A form with validation that creates and edits models | Booking form (create and reschedule), profile, reviews, instructor profile, skill ratings | `bookings/forms.py`, `register-validation-errors-desktop.png`, `booking-postcode-outside-area-desktop.png` |
| 1.5 Consistent, logical Django file structure | Standard per-app layout: models, forms, views, urls, admin, tests, templates, migrations | Repository |
| 1.6 Clean code | Descriptive names, comments in every file, separate HTML/CSS/JS/Python | `docs/testing/flake8.txt`, `docs/testing/jshint.txt` |
| 1.7 URLs defined consistently | Namespaced URLs `/<app>/<object>/<action>/` | `*/urls.py` |
| 1.8 Main navigation and structured layout | `templates/base.html` nav, which changes for visitors, learners and the instructor | Screenshots |
| 1.9 Custom Python logic | Booking rules, slot generation, postcode districts, package hour balance, test-ready score | `bookings/services.py`, `core/postcodes.py`, `packages/models.py`, `progress/models.py` |
| 1.10 Functions with compound statements (if/loops) | e.g. `available_start_times`, `booking_problems`, `progress_summary`, `SkillRatingsForm.save` | Same files |
| 1.11 Manual or automated testing of functionality, usability, responsiveness, data | 130 automated tests, axe-core accessibility, console and link checks, manual test table, screenshots at desktop and mobile sizes | `docs/testing/test-results.txt`, README → Testing |
| 2.1 Relational schema with clear relationships | User, Profile, Instructor, Booking, Payment, LessonPackage, PackagePurchase, Review, Skill, SkillRating | README → Data schema (ERD) |
| 2.2 At least two custom models | Nine custom models | `*/models.py` |
| 2.3 A form that creates records (besides auth) | Booking, review, package purchase, skill ratings | `bookings/forms.py`, `instructors/forms.py` |
| 2.4 Full CRUD | Bookings (create/read/reschedule/cancel), reviews, profile, skill ratings | README → CRUD summary |
| 3.1 Registration and login, with a reason to sign up | Needed to book, pay, keep progress and package hours | `accounts/` |
| 3.2 Login and registration pages only for anonymous users | Logged-in users are redirected | `accounts/tests.py::test_login_and_register_redirect_logged_in_users` |
| 3.3 Non-admins can't access the data store directly | Only staff use `/admin/`; ownership checks on every view | `bookings/tests.py` permission tests; `learner-blocked-from-diary-desktop.png` |
| 4.1 E-commerce with an online payment system | Stripe Checkout for lessons and for packages, webhooks, refunds | `payments/`, `packages/` |
| 4.2 Feedback on successful and unsuccessful purchases | Success, cancel and error messages, "you have not been charged" | `payments/templates/`, `payments/tests.py` |
| 5.1 Deployed to a hosting platform, matches development | Render + Neon; the same commit is tested locally, in CI and in Render's build | https://drx-hec8.onrender.com, `build.sh` |
| 5.2 No commented-out code, no broken internal links | No commented-out code; every internal link followed by the browser check | `docs/testing/link-check.txt`, `core/tests.py` |
| 5.3 Security: no secrets in Git, DEBUG off | Environment variables only, `env.py` git-ignored, DEBUG defaults to False, HTTPS and HSTS | `drx/settings.py`, `.gitignore` |
| 5.4 Git version control with regular commits | Small, descriptive commits throughout | `git log` |
| 5.5 Well-structured README in consistent Markdown | 14 numbered sections from rationale to attribution | `README.md`, `TESTING.md` |
| 5.6 Deployment procedure (incl. database) and testing procedure documented | Render + Neon + Stripe steps; automated and manual testing | README → Deployment, Testing |

## Merit criteria

| Criterion | Evidence |
|---|---|
| M(i) Real-world app, easy to navigate, user in control, CRUD reflected immediately, clear purpose | Built for my own driving school; messages after every action; confirmation pages; live availability |
| M(ii) Robust codebase | Stripe outages and missing keys handled, no double booking, 24-hour cut-off, refund failures flagged |
| M(iii) TDD shown in commits | Test commits come before or with each feature; the CI runs on every push |
| M(iv) Procfile, requirements, settings; data store in one place | `Procfile`, `requirements.txt`, `render.yaml`, `build.sh`; database only via `DATABASE_URL` |
| M(v) Data schema fully described in README | README section 6: ERD, relationships and deletion table, a field table for every model |
| M(vi) Django template logic used well | Template inheritance, includes, filters; business logic in views and services, data logic in models |
| M(vii) Version control used effectively | Branch + pull request, CI checks on the PR |

## Before you hand it in

- [x] Connect the Neon database (`DATABASE_URL` on Render)
- [x] Wireframes in `docs/wireframes/` (you can add photos of your own sketches too)
- [x] Tests, flake8, JSHint, W3C HTML and CSS all passing (`docs/testing/`)
- [x] Screenshots at desktop and mobile sizes (`docs/screenshots/`)
- [ ] Add Stripe **test** keys and the webhook on Render, then do one test payment
- [ ] Change the admin password you were given
- [ ] Repeat the manual test table (README → Testing) on the live site
- [ ] Add your own photo and bio under *Edit profile* (optional)
