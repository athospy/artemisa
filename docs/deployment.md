# Deploying Artemisa

Production is one Ubuntu server: Gunicorn (systemd, user `www-data`) behind Nginx, with
PostgreSQL on the same machine. GitHub Actions deploys every commit on `main` that passes
the tests.

## How a change reaches production

1. A pull request runs **Tests** (`.github/workflows/test.yml`): the Django test suite on
   Python 3.10 against Postgres 17. The Anthropic API is mocked, so CI needs no key.
2. Merging to `main` runs **Tests** again. Only if it passes does **Deploy to Production**
   (`.github/workflows/deploy.yml`) start, and it checks out exactly the tested commit.
3. The deploy rsyncs the code to the server (never `.env`, the top-level `static/` or
   `media/`), installs requirements, runs `migrate` and `collectstatic`, and restarts
   Gunicorn.

A deploy can also be started by hand from the Actions tab ("Run workflow").

Repository secrets used by the deploy: `PROD_SSH_KEY`, `PROD_SSH_HOST`, `PROD_SSH_USER`,
`PROD_PROJECT_PATH`, and optionally `PROD_GUNICORN_SERVICE` / `PROD_NGINX_SERVICE`.

## Server setup (once)

```bash
git clone <repository-url> /srv/artemisa
cd /srv/artemisa
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

`/srv/artemisa/.env` (production values; see `.env.example` for every name):

```bash
DJANGO_SECRET_KEY=<generate: python -c "from django.core.management.utils import get_random_secret_key as g; print(g())">
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your.domain
CSRF_TRUSTED_ORIGINS=https://your.domain
DB_NAME=artemisa
DB_USER=artemisa
DB_PASSWORD=<strong password>
DB_HOST=localhost
DB_PORT=5432
```

Gunicorn runs as `www-data` and must be able to read it:

```bash
sudo chown root:www-data .env && sudo chmod 640 .env
```

Database, static files, first user and the public demo:

```bash
venv/bin/python manage.py migrate
venv/bin/python manage.py collectstatic --noinput
venv/bin/python manage.py createsuperuser
sudo -u www-data venv/bin/python manage.py seed_demo
```

### Gunicorn (systemd)

```ini
# /etc/systemd/system/artemisa.service
[Unit]
Description=Artemisa Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/srv/artemisa
Environment="PATH=/srv/artemisa/venv/bin"
ExecStart=/srv/artemisa/venv/bin/gunicorn capstone.wsgi:application --bind 127.0.0.1:8001 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now artemisa
```

### Nginx

```nginx
server {
    listen 80;
    server_name your.domain;

    location /static/ {
        alias /srv/artemisa/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then add HTTPS (for example with Certbot) and check: the home page, `/demo/`, `/admin/`, and
that static files load.

## Lessons from running it

- If Gunicorn fails to start with `PermissionError: '.env'`, the file lost its
  `www-data` group (the deploy restores it after its `chown`).
- Run `seed_demo` again at any time to reset the public demo; it never touches real events.
