# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Artemisa is a Django scoring and tournament management system for archery competitions: managing archers/categories/competitions, entering end-by-end scores on a touch-screen scoreboard, running a shoot timer, and displaying live results on a spectator screen. Backend is Django + PostgreSQL; frontend is server-rendered templates (Bootstrap 4) with vanilla JavaScript doing the real-time scoring/timer/results logic (no JS framework, no build step).

## Commands

```bash
# Start the Postgres database (Docker)
docker compose up -d db

# Python env + deps
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Migrations
python manage.py makemigrations
python manage.py migrate

# Run dev server
python manage.py runserver

# Run tests (artemisa/tests.py is currently empty — no test suite exists yet)
python manage.py test
```

Config is read from `.env` (see `.env.example`) via `python-dotenv`: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

## Architecture

### Project layout

- `capstone/` — the actual active Django project package (`DJANGO_SETTINGS_MODULE=capstone.settings`, root `urls.py`, wsgi/asgi). This is the one in use.
- `santi/` — a **stale leftover duplicate** of `capstone/settings.py` from an earlier project name. It is not referenced by `manage.py` or any entry point. Don't edit it thinking it's live config; if working on settings, `capstone/settings.py` is the source of truth.
- `artemisa/` — the single Django app containing all models, views, templates, static assets, and URLs for the product.

### Domain model (`artemisa/models.py`)

```
Competition ──┐
Category ─────┼──► Registration ──► Score (one per arrow)
Archer ───────┘
```

- `Registration` is the join row linking one `Archer` to one `Category` within one `Competition` (unique constraint on the triple).
- `Score` belongs to a `Registration` and represents a single arrow: `end_number` (1–12, i.e. up to 12 ends per round) × `shoot_number` (1–6 arrows per end), unique together. `score` is a `CharField` validated against `{0-10, X, M}` — **X counts as 10 points and also as an X for tiebreakers, M counts as 0**. This scoring convention is duplicated in both `views.py` (SQL `Case`/`When` expressions) and `compete.js` (client-side tally) — keep both in sync if it changes.
- Custom permissions on `Competition.Meta`: `can_score`, `can_view_results`, `can_use_timer` — intended for role-based access beyond plain `login_required`, though views currently only check `login_required`.

### Request flow / view categories (`artemisa/views.py`, `artemisa/urls.py`)

- **Page views** (`index`, `competitions`, `select_competition`, `compete`, `result_screen`, `shoot_timer`) render full templates extending `layout.html`.
- **AJAX endpoints** (`add_archer_div`, `add_score_div`, `save_score_db`, `result_category`, `get_archer_scores`) are POST-only, read a JSON body via `json.loads(request.body)`, and either return an HTML fragment (for `insertAdjacentHTML` injection — e.g. `archer_div.html`, `score_div.html`) or a `JsonResponse` (for results polling).
- **Session-carried competition**: `select_competition` stores the chosen competition as JSON in `request.session['current_competition']`. Downstream AJAX endpoints (`save_score_db`, `result_category`, `get_archer_scores`) read the competition id back out of the session instead of taking it as a URL/body param — if you add a new endpoint that needs the current competition, follow this same session pattern rather than threading it through the URL.
- `result_category` computes ranking via DB aggregation (`Sum`/`Case`/`Coalesce`, plus a `Subquery` for last-end total) ordered by `total_score`, `tens_count`, `xs_count`, `last_end_total` — this is the tiebreaker chain, so preserve that ordering if touched.

### Frontend

- No bundler; each feature has one hand-written JS file under `artemisa/static/artemisa/`: `compete.js` (scoreboard — score entry, running totals, KioskBoard virtual keyboard for touch input), `shoot_timer.js` (prep/competition/finish phase state machine with audio cues), `results.js` (auto-rotates the results display through categories every 3s).
- Templates in `artemisa/templates/` extend `layout.html` (Bootstrap 4 navbar/blocks). `archer_div.html` and `score_div.html` are partials returned by AJAX views and injected client-side, not rendered as full pages.

### Deployment

`.github/workflows/deploy.yml` deploys on push to `main`: rsyncs the repo to the prod server over SSH, then remotely creates/activates a venv, installs deps, runs `migrate` + `collectstatic`, fixes `www-data` ownership on `static/`/`media/`, and restarts the `artemisa_gunicorn` systemd service + reloads nginx. Gunicorn/nginx/systemd unit setup itself is documented in `readme.md`.

## Notes

- `PROJECT_DOCUMENTATION.md` is a detailed but partially stale architecture writeup (e.g. it describes views as unauthenticated and `result_category` as a naive Python loop) — where it conflicts with the current code in `views.py`/`models.py`, trust the code.
