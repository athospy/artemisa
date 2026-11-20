# Artemisa - Archery Tournament Scoring System

Artemisa is a sophisticated and user-friendly scoring system designed specifically for archery tournaments. This project was born out of a necessity to streamline and modernize the way archery competitions are managed, scored, and displayed. Traditional methods of scoring and timekeeping in archery can be cumbersome, error-prone, and lacking in real-time visibility. Artemisa addresses these challenges by offering an integrated solution that not only simplifies the process but also enhances the experience for archers, judges, and spectators alike.

## Project Overview

Artemisa stands out due to its comprehensive feature set and thoughtful design. Unlike other generic scoring systems, Artemisa is tailored for archery, taking into account the unique requirements of this sport. From managing participants and categories to handling real-time scoring and displaying results on large screens, every aspect of the tournament is covered. The system ensures accuracy, efficiency, and transparency, which are crucial for maintaining the integrity and excitement of the competition.

The development of Artemisa was driven by the need to eliminate manual errors and to provide a seamless experience for all stakeholders. The complexity of this project lies in its multifaceted approach to solving the various logistical problems associated with archery tournaments. The project required a deep understanding of both the sport and the technological solutions that could enhance it. This included developing a robust backend to handle data management, a responsive frontend for user interaction, and real-time capabilities for scoring and timekeeping.

## Distinctiveness and Complexity

Artemisa distinguishes itself from other projects in several key ways:

1. **Domain-Specific Design**: Unlike general-purpose scoring systems, Artemisa is designed specifically for archery. This focus allowed us to incorporate features that are particularly relevant to archery tournaments, such as category-specific scoring with data validation, timed phases for preparation and competition, and specialized result displays that changes automatically.

2. **Real-Time Functionality**: Implementing real-time scoring and timekeeping was a significant technical challenge. The system had update scores instantly, and keep looping trough the catetories indefinely;

3. **User Experience**: A major goal of Artemisa was to create an intuitive and user-friendly interface. This required extensive frontend development and user testing to ensure that the system could be used easily by archers, judges, and spectators of all technological proficiencies.

4. **Scalability and Reliability**: The system was designed to handle large-scale tournaments with potentially hundreds of participants. Ensuring that the system remained responsive and reliable under heavy load was a key consideration using mostly javacript that runs on the client for the procesing information and make calculations.

## Features

- **Simple Management**: Easily add, update, and manage archers, categories and competitions in the tournament using Django administration features.
- **Registration Management**: Register archers for specific categories within a competition.
- **Scoring System**: Record and track the score of each archer after every round, with scores grouped by categories for easy tracking.
- **Shoot Timer**: with sound cues in each phase and a 10 second warning sound for the competition phase time.
  - **Preparation Phase**: 10 seconds for archers to prepare before the competition begins.
  - **Competition Phase**: 3 minutes for each round of shooting.
- **Result Display**: Show current standings and scores of all archers in each category on a large screen, allowing everyone to see the competition's progress and current leaders.

## Important Files

Here is an overview of the key files and their roles within the Artemisa project:

- **layout.html**: Located in the `templates` folder, this file uses Bootstrap for styling and provides a simple, intuitive navbar. It includes blocks for the main content in the body section and necessary JavaScript files in the head section to ensure a cohesive and responsive design across all pages.

- **competition.html**: Found in the `templates` folder, this is the central hub of the project. From this page, you can navigate to the different components of the system: the scoreboard, the shoot timer, and the results screen. It serves as the main entry point for managing and viewing the competition details.

- **compete.html and compete.js**:
  - **compete.html**: This template is responsible for the scoreboard functionality. It allows you to select the competing category and the archers within that category. You can add scores for each end, and the system automatically accumulates these scores, keeping track of the total for each archer. There is also a button to select the current archer who is shooting, enabling score entry for each individual.
  - **compete.js**: Located in the `static` folder, this JavaScript file supports the functionality of the `compete.html` template, handling the dynamic aspects of score tracking and archer management.

- **shoot_timer.html and shoot_timer.js**:
  - **shoot_timer.html**: This template displays the timer for each phase of the competition. It visually represents the preparation and competition phases, providing a clear and structured countdown for participants.
  - **shoot_timer.js**: Also located in the `static` folder, this script manages the timer's functionality, including playing sounds for each event to alert participants visually and audibly to the current phase.

- **result_screen.html and results.js**:
  - **result_screen.html**: This template displays the competition results, ordering them in descending order based on the scores for each category. It provides a clear and concise view of the current standings.
  - **results.js**: Found in the `static` folder, this script enables the automatic looping of results every 3 seconds, cycling through the categories to ensure that the latest standings are continuously visible.


## Installation and Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

### Quick Start

1. **Clone the repository**:

    ```bash
    git clone <repository-url>
    cd artemisa
    ```

2. **Start the database**:

    ```bash
    docker compose up -d db
    ```

    This will:
    - Pull and run Postgres 17 in a Docker container
    - Create the database with persistent storage
    - Expose the database on port 54322

3. **Set up Python virtual environment**:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

    If `requirements.txt` doesn't exist, install the required packages:
    ```bash
    pip install django psycopg2-binary gunicorn
    ```

5. **Configure environment variables** (optional):

    Create a `.env` file in the project root:
    ```bash
    DJANGO_SECRET_KEY=your-secret-key-here
    DJANGO_DEBUG=True
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,artemisa.lajota.com.py
    DB_NAME=artemisa
    DB_USER=artemisa
    DB_PASSWORD=artemisa
    DB_HOST=localhost
    DB_PORT=54322
    ```

6. **Run migrations**:

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

7. **Create a superuser**:

    ```bash
    python manage.py createsuperuser
    ```

8. **Run the development server**:

    ```bash
    python manage.py runserver
    ```

9. **Access the application**:

    Open your web browser and go to `http://127.0.0.1:8000/` to access Artemisa.

### Running the Project

After initial setup, to run the project:

1. **Start the database** (if not already running):
    ```bash
    docker compose up -d db
    ```

2. **Activate virtual environment**:
    ```bash
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Run the server**:
    ```bash
    python manage.py runserver
    ```

### Stopping the Services

- **Stop the database**:
    ```bash
    docker compose down
    ```

- **Stop the database and remove volumes** (deletes all data):
    ```bash
    docker compose down -v
    ```

### Database Management

- **Connect to the database**:
    ```bash
    PGPASSWORD=artemisa psql -h localhost -p 54322 -U artemisa -d artemisa
    ```

- **View database logs**:
    ```bash
    docker compose logs db
    ```

- **Backup the database**:
    ```bash
    docker exec artemisa-db pg_dump -U artemisa -Ft artemisa > backup.tar
    ```

- **Restore from backup**:
    ```bash
    docker exec -i artemisa-db pg_restore -U artemisa --clean --if-exists -d artemisa < backup.tar
    ```

## Deployment

Below are two deployment approaches: a quick Docker-based development deploy and a production-ready stack with Gunicorn + Nginx.

### Option A: Quick Deploy (Local Docker DB + Django)

- **Prerequisites:** Docker, Python, a `.env` configured as in Installation.

1. Start Postgres:
    ```bash
    docker compose up -d db
    ```
2. Activate venv and install deps:
    ```bash
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3. Apply migrations and collect static:
    ```bash
    python manage.py migrate
    python manage.py collectstatic --noinput
    ```
4. Run with Gunicorn (recommended over runserver):
    ```bash
    gunicorn capstone.wsgi:application --bind 0.0.0.0:8000 --workers 3
    ```

You can put Gunicorn behind a reverse proxy (e.g., Caddy or Nginx) locally if desired.

### Option B: Production Deploy (Ubuntu/Debian server)

- **Prerequisites:** A VM with Docker, Git, Python 3.11+, domain/DNS pointed to server.

1. Clone project and set environment:
    ```bash
    git clone <repository-url>
    cd artemisa
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
2. Configure `.env` with production values:
    ```bash
    DJANGO_SECRET_KEY=<strong-unique-secret>
    DJANGO_DEBUG=False
    DJANGO_ALLOWED_HOSTS=your.domain,localhost
    CSRF_TRUSTED_ORIGINS=https://your.domain
    DB_NAME=artemisa
    DB_USER=artemisa
    DB_PASSWORD=artemisa
    DB_HOST=127.0.0.1
    DB_PORT=5432
    ```
3. Provision Postgres (Docker):
    ```bash
    docker compose up -d db
    ```
4. Apply migrations and collect static files:
    ```bash
    python manage.py migrate
    python manage.py collectstatic --noinput
    ```
5. Run Gunicorn as a systemd service:
    ```bash
    sudo tee /etc/systemd/system/artemisa.service > /dev/null << 'EOF'
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
    EOF
    sudo systemctl daemon-reload
    sudo systemctl enable --now artemisa
    ```
    Adjust `WorkingDirectory` and paths to your repo location.

6. Configure Nginx reverse proxy:
    ```bash
    sudo tee /etc/nginx/sites-available/artemisa > /dev/null << 'EOF'
    server {
        listen 80;
        server_name your.domain;

        location /static/ {
            alias /srv/artemisa/artemisa/static/;
        }

        location / {
            proxy_pass http://127.0.0.1:8001;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    EOF
    sudo ln -s /etc/nginx/sites-available/artemisa /etc/nginx/sites-enabled/artemisa
    sudo nginx -t && sudo systemctl restart nginx
    ```

7. Create superuser (first-time setup):
    ```bash
    source /srv/artemisa/venv/bin/activate
    cd /srv/artemisa
    python manage.py createsuperuser
    ```

### Post-Deploy Checklist

- Verify `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` include your domain.
- Confirm database connectivity and migrations.
- Check static files are served correctly.
- Ensure admin is accessible at `/admin` and results/compete/timer pages load.

## Committing Changes

Use the following commands to commit and push the latest work:

```bash
git add .
git commit -m "Home redesign, favicon, results fix, timer stages, score restore"
git push origin main
```

## Use it from Claude (MCP server)

Artemisa ships a small, read-only [MCP](https://modelcontextprotocol.io) server, so Claude
Desktop or Claude Code can answer questions about your tournaments ("who is leading
Recurve Bow Women?", "show me Lucía's scorecard"). It runs locally over stdio and reads the
database your `.env` points at. No tool writes data, returns archer emails, or calls the
Anthropic API.

| Tool | What it returns |
|---|---|
| `list_competitions` | Competitions with ids, dates, categories and archer counts |
| `get_leaderboard` | Ranked archers (score, 10s, Xs, last end) for one category or all |
| `get_archer_scorecard` | One archer's arrows end by end, running total and rank |
| `get_match_recap` | The saved AI recap, if it matches the current standings |

Try it on the demo tournament: `python manage.py seed_demo`.

**Claude Code** (from the repo folder):

```bash
claude mcp add artemisa -- "$PWD/venv/bin/python" "$PWD/manage.py" mcp
```

**Claude Desktop** (`claude_desktop_config.json`, use absolute paths):

```json
{
  "mcpServers": {
    "artemisa": {
      "command": "/path/to/artemisa/venv/bin/python",
      "args": ["/path/to/artemisa/manage.py", "mcp"]
    }
  }
}
```

## Usage

### Archer Management

- Navigate to the Archer Management section to add, update, or delete archers.

### Category Management

- Define and manage different categories for the tournament in the Category Management section.

### Competition Management

- Create and manage competitions, and register archers for specific categories.

### Scoring System

- Select a competition and navigate to the scoring section.
- Record the score of each archer after every round.
- Scores are grouped by categories for easy tracking.

### Shoot Timer

- Use the shoot timer to manage the phases of the competition:
  - **Preparation Phase**: 10 seconds for preparation.
  - **Competition Phase**: 3 minutes for each round of shooting.

### Result Display

- Navigate to the result screen to display current standings and scores on a large screen.
- This allows everyone to see the competition progress and know who is leading in each category.
- It automatically change category each 3 seconds.

---

Artemisa is not just a tool; it's a step towards modernizing and enhancing the experience of archery tournaments. By addressing the specific needs of archery competitions and providing a robust, real-time solution, Artemisa aims to set a new standard in sports scoring systems. Whether you're an archer, a judge, or a spectator, Artemisa ensures that the tournament runs smoothly, scores are accurately recorded, and results are transparently displayed. I am proud of the complexity and the thoughtful design that went into Artemisa and believe it stands out as a distinctive and impactful project in the realm of sports technology.
# artemisa
