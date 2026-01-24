# Changelog

## [Recent Updates] - January 2026

### Added

#### Docker Compose Integration
- Added `docker-compose.yml` to orchestrate the Postgres database service
- Configured Postgres 17 container with:
  - Container name: `artemisa-db`
  - Port mapping: `54322:5432`
  - Persistent volume: `db_data` for data persistence
  - Health checks for service readiness
  - Environment variables for DB configuration

#### Database Configuration
- Updated Django settings to use environment variables for database connection
- Default database credentials aligned with Docker Compose setup:
  - `DB_NAME`: artemisa
  - `DB_USER`: artemisa
  - `DB_PASSWORD`: artemisa
  - `DB_HOST`: localhost
  - `DB_PORT`: 54322

#### Security Enhancements
- Externalized `SECRET_KEY` to environment variable with fallback
- Configured `DEBUG` mode via environment variable
- Externalized `ALLOWED_HOSTS` to environment variable
- Configured `CSRF_TRUSTED_ORIGINS` via environment variable

#### UI/UX Improvements
- Redesigned home page with hero, preview tiles, feature cards, and live metrics
- Added favicon and theme color for better browser integration
- Improved `compete` UX with toggle-based archer selection and auto-restore of saved ends

#### Results and Timer
- Fixed results aggregation: correct joins to `Score` from `Registration` and proper tie-breakers
- Timer stage text added: "Get Ready", "Shoot", "Almost Time Out", and "Time Out"

### Changed

#### Settings Management
- Moved sensitive configuration from hardcoded values to environment variables in `santi/settings.py`
- Updated default database user from `postgres` to `artemisa` to match container setup
- Database configuration now fully configurable via environment variables

### Infrastructure

#### Development Environment
- Postgres 17 running in Docker container
- Database backup restored: `dump-artemisa-202601231633.tar`
- All application tables verified and operational:
  - `artemisa_archer`
  - `artemisa_category`
  - `artemisa_competition`
  - `artemisa_registration`
  - `artemisa_score`
  - Django auth and admin tables

### Technical Details

#### Docker Container Setup
- Image: `postgres:17`
- Automatic restart policy: `unless-stopped`
- Healthcheck interval: 10 seconds
- Connection timeout: 5 seconds
- Max retries: 5

#### Environment Variables Support
The following environment variables can be configured:
- `DJANGO_SECRET_KEY`: Django secret key for cryptographic signing
- `DJANGO_DEBUG`: Enable/disable debug mode (default: True)
- `DJANGO_ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `CSRF_TRUSTED_ORIGINS`: Comma-separated list of trusted origins for CSRF
- `DB_NAME`: Database name (default: artemisa)
- `DB_USER`: Database user (default: artemisa)
- `DB_PASSWORD`: Database password (default: artemisa)
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 54322)

### Benefits

1. **Reproducible Environment**: One-command database setup with Docker Compose
2. **Environment Flexibility**: Easy configuration via environment variables
3. **Data Persistence**: Docker volumes ensure data survives container restarts
4. **Health Monitoring**: Automated health checks ensure database availability
5. **Security**: Sensitive data no longer hardcoded in settings
6. **12-Factor Compliance**: Configuration separated from code

### Deployment
- README updated with deployment guides for local (Gunicorn) and production (Gunicorn + Nginx) and commit instructions
