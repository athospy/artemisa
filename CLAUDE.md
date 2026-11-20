# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Artemisa is a Django scoring and tournament management system for archery competitions: managing archers/categories/competitions, entering end-by-end scores on a touch-screen scoreboard, running a shoot timer, displaying live results on a spectator screen, and writing an AI match recap with Claude. Backend is Django + PostgreSQL; frontend is server-rendered templates (Bootstrap 4) with vanilla JavaScript doing the real-time scoring/timer/results logic (no JS framework, no build step).

## Commands

```bash
# Start the Postgres database (Docker, port 54322)
docker compose up -d db

# Python env + deps (Python 3.10+; production runs 3.10)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Migrations
python manage.py makemigrations
python manage.py migrate

# Demo tournament (made-up archers, with its saved AI recap)
python manage.py seed_demo

# Run dev server
python manage.py runserver

# Run tests (the Anthropic API is mocked; no API key needed)
python manage.py test artemisa

# Grounding eval for the AI recap (real, paid API calls)
python manage.py eval_recap --runs 10 --out evals/recap_grounding.json

# Read-only MCP server over stdio
python manage.py mcp
```

Config is read from `.env` (see `.env.example`) via `python-dotenv`: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, and optionally `ANTHROPIC_API_KEY` (only needed to generate new AI recaps — see below). Since `load_dotenv()` populates `os.environ`, the `anthropic` SDK picks up `ANTHROPIC_API_KEY` automatically without it being threaded through `settings.py`.

## Architecture

### Project layout

- `capstone/` — the Django project package (`DJANGO_SETTINGS_MODULE=capstone.settings`, root `urls.py`, wsgi/asgi).
- `artemisa/` — the single Django app containing all models, views, templates, static assets, and URLs for the product.
- `evals/` — saved results of `eval_recap`. `docs/` — deployment guide and README screenshots.

### Domain model (`artemisa/models.py`)

```
Competition ──┐
Category ─────┼──► Registration ──► Score (one per arrow)
Archer ───────┘
```

- `Registration` is the join row linking one `Archer` to one `Category` within one `Competition` (database unique constraint `unique_archer_registration` on the triple).
- `Score` belongs to a `Registration` and represents a single arrow: `end_number` (1–12, i.e. up to 12 ends per round) × `shoot_number` (1–6 arrows per end), unique together (`unique_score_per_arrow`). `score` is a `CharField` validated against `{0-10, X, M}` — **X counts as 10 points and also as an X for tiebreakers, M counts as 0**. This scoring convention lives in `standings.py` (SQL `Case`/`When` expressions) and is duplicated in `compete.js` (client-side tally) — keep both in sync if it changes.
- `Competition.is_demo` marks the public demo competition (visible without login). `Competition.ai_recap` / `ai_recap_input` store the saved AI recap and the exact standings text it was written from.
- Custom permissions on `Competition.Meta`: `can_score`, `can_view_results`, `can_use_timer` — intended for role-based access, though views currently only check `login_required`.

### Ranking, recap and MCP modules

- `standings.py` — the one ranking query. `category_ranking(competition_id, category_id)` aggregates total, 10s, Xs and last-end points in PostgreSQL and orders by `total_score`, `tens_count`, `xs_count`, `last_end_total` (the tiebreaker chain — preserve it), then name. `competition_standings(competition)` returns every category (ordered by name). The results screen, the AI recap and the MCP server all use it.
- `recap.py` — `recap_input()` turns the standings into the prompt text, `saved_recap()` returns the stored recap if its input still matches, `generate_recap()` calls the Anthropic API (model `claude-opus-5-5`, plain-text system prompt limited to facts in the standings).
- `grounding.py` — deterministic check that every number and two-word name in a recap comes from the standings. Used by `seed_demo --refresh-recap` (refuses a failing recap), `generate_match_recap` (logs a warning) and `eval_recap`.
- `mcp_tools.py` + `management/commands/mcp.py` — read-only MCP server (`list_competitions`, `get_leaderboard`, `get_archer_scorecard`, `get_match_recap`). Never returns archer emails and never calls the Anthropic API.
- `management/commands/seed_demo.py` — creates/resets "Artemisa Demo Open" and attaches the committed recap from `demo_recap.json`.

### Request flow / view categories (`artemisa/views.py`, `artemisa/urls.py`)

- **Public pages**: `index` and `demo` (renders the demo competition read-only). `result_screen`, `shoot_timer` and `match_recap` are public for the demo competition only (`_can_view`); other competitions redirect to login. There is no public sign-up; organizer accounts are created with `createsuperuser` or the admin.
- **Organizer page views** (`competitions`, `select_competition`, `compete`) are `login_required` and render full templates extending `layout.html`.
- **CRUD form views** (`add_competition`, `add_category`, `add_archer`, `add_registration`) all follow the same shape: a `ModelForm` from `forms.py`, GET renders it blank, POST validates + saves + redirects to `competitions`. Follow this pattern for any new simple create form rather than inventing a new one.
- **AJAX endpoints** (`add_archer_div`, `add_score_div`, `save_score_db`, `result_category`, `get_archer_scores`, `generate_match_recap`) are POST-only, read a JSON body via `json.loads(request.body)` (where applicable), and either return an HTML fragment (for `insertAdjacentHTML` injection — e.g. `archer_div.html`, `score_div.html`) or a `JsonResponse` (for results polling and the recap text).
- **Session-carried competition**: `select_competition` stores the chosen competition as JSON in `request.session['current_competition']`. The scoring endpoints (`save_score_db`, `get_archer_scores`) read the competition id from the session. `result_category` takes `competition_id` from the body (so the public demo works without a session) and falls back to the session.
- **AI match recap** (`match_recap` renders the page with the saved recap, `generate_match_recap` does the work): returns the saved recap while the standings are unchanged; otherwise, for logged-in organizers only, generates a new one and saves it. Anonymous visitors never trigger an API call (404 if there is no saved recap). Fails soft with a `JsonResponse` error (400 if no scores yet, 502 if the API call raises) rather than a 500 — keep that behavior if touched, since this runs live during a tournament and a hard error would break the page.

### Frontend

- No bundler; each feature has one hand-written JS file under `artemisa/static/artemisa/`: `compete.js` (scoreboard — score entry, running totals, KioskBoard virtual keyboard for touch input, restores saved ends in order after a reload), `shoot_timer.js` (prep/competition/finish phase state machine with audio cues), `results.js` (auto-rotates the results display through categories every 3s), `match_recap.js` (the organizer's "generate recap" button).
- Templates in `artemisa/templates/` extend `layout.html` (Bootstrap 4 navbar/blocks). `archer_div.html` and `score_div.html` are partials returned by AJAX views and injected client-side, not rendered as full pages.

### Tests and CI

- `artemisa/tests.py` holds the test suite (demo access, saved recap with the API mocked, seed_demo, MCP tools, grounding check, eval command, database constraints).
- `.github/workflows/test.yml` runs on every pull request and push to `main` against a Postgres service on Python 3.10: `manage.py check`, `makemigrations --check --dry-run` (fails if a model change has no migration), then the tests.

### Deployment

`.github/workflows/deploy.yml` runs only after the "Tests" workflow succeeds on a push to `main` (or by hand), and deploys exactly the commit that was tested: rsyncs the repo to the prod server over SSH, then remotely creates/activates a venv, installs deps, runs `migrate` + `collectstatic`, fixes `www-data` ownership on `static/`/`media/` (and keeps `.env` readable by `www-data`), and restarts the `artemisa_gunicorn` systemd service + reloads nginx. Server setup (gunicorn, nginx, systemd) is in `docs/deployment.md`.
