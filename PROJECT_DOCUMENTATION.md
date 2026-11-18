# Artemisa - Comprehensive Project Documentation

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Database Design](#database-design)
4. [Features Deep Dive](#features-deep-dive)
5. [Technical Implementation](#technical-implementation)
6. [User Workflows](#user-workflows)
7. [Security Considerations](#security-considerations)
8. [Improvements and Recommendations](#improvements-and-recommendations)

---

## Executive Summary

**Artemisa** is a specialized web-based scoring and tournament management system designed exclusively for archery competitions. Built with Django 5.0.7 on the backend and vanilla JavaScript on the frontend, the system addresses critical pain points in traditional archery tournament management: manual scoring errors, lack of real-time visibility, cumbersome timekeeping, and poor spectator experience.

### Project Context
- **Built with**: Django 5.0.7, PostgreSQL, Bootstrap 4, Vanilla JavaScript
- **Architecture**: Monolithic Django application with client-side heavy JavaScript
- **Database**: PostgreSQL (artemisa database)
- **Deployment**: Gunicorn WSGI server, accessible at artemisa.lajota.com.py
- **Environment**: Python 3.11 virtual environment (aremisaenv)

### Core Value Proposition
Unlike generic scoring systems, Artemisa is purpose-built for archery, incorporating sport-specific features like:
- Category-based competition management
- End-by-end scoring with automatic X/10/M validation
- Timed shooting phases (10s preparation, 3min competition)
- Real-time result displays with automatic rotation
- Touch-optimized virtual keyboard for score entry

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Browser                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  compete.js  │  │shoot_timer.js│  │  results.js  │      │
│  │ (426 lines)  │  │  (98 lines)  │  │  (95 lines)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────────┬─────────────────────────────────┘
                            │ AJAX/Fetch API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Django Application                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Views Layer                        │  │
│  │  - index, competitions, select_competition           │  │
│  │  - compete (scoring interface)                       │  │
│  │  - add_score_div, add_archer_div (AJAX endpoints)   │  │
│  │  - save_score_db (persist scores)                   │  │
│  │  - result_screen, result_category (display)         │  │
│  │  - shoot_timer (timing interface)                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Models Layer                       │  │
│  │  Competition → Registration ← Category                │  │
│  │       ↑             ↑              ↑                  │  │
│  │       └────Archer───┴──────Score───┘                 │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │ Django ORM
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database (artemisa)                  │
│  Tables: competition, category, archer, registration, score │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend**:
- **Django 5.0.7**: Web framework
- **psycopg2-binary 2.9.9**: PostgreSQL adapter
- **gunicorn 22.0.0**: WSGI HTTP server
- **asgiref 3.8.1**: ASGI framework components
- **sqlparse 0.5.0**: SQL parsing utilities

**Frontend**:
- **Bootstrap 4.5.0**: UI framework
- **Bootstrap Icons**: Icon library
- **KioskBoard 2.3.0**: Virtual keyboard for touch-screen scoring
- **Vanilla JavaScript**: No framework dependencies
- **Google Fonts (Orbitron)**: Custom typography for timers

**Database**:
- **PostgreSQL**: Primary data store
- Credentials: artemisa/artemisa (localhost)

### Directory Structure Analysis

```
artemisa/
├── manage.py                    # Django management script
├── readme.md                    # Basic documentation
├── aremisaenv/                  # Virtual environment (Python 3.11)
│
├── artemisa/                    # Main application package
│   ├── models.py                # Data models (5 models)
│   ├── views.py                 # View logic (165 lines, 10 views)
│   ├── urls.py                  # URL routing (10 routes)
│   ├── forms.py                 # Form definitions (incomplete/broken)
│   ├── admin.py                 # Admin interface config
│   ├── apps.py                  # App configuration
│   ├── tests.py                 # Test suite (likely empty)
│   │
│   ├── static/artemisa/         # Static assets
│   │   ├── compete.js           # Scoring logic (426 lines)
│   │   ├── shoot_timer.js       # Timer logic (98 lines)
│   │   ├── results.js           # Results display (95 lines)
│   │   ├── styles.css           # Custom styles
│   │   ├── kioskboard-2.3.0.*   # Virtual keyboard library
│   │   ├── whistle.wav          # Timer start/stop sound
│   │   └── warning.mp3          # 10-second warning sound
│   │
│   ├── templates/               # HTML templates
│   │   ├── layout.html          # Base template (92 lines)
│   │   ├── home.html            # Landing page
│   │   ├── competitions.html    # Competition list
│   │   ├── competition.html     # Competition hub
│   │   ├── compete.html         # Scoring interface
│   │   ├── shoot_timer.html     # Timer interface
│   │   ├── result_screen.html   # Results display
│   │   ├── archer_div.html      # Archer scoring component
│   │   └── score_div.html       # Score input row component
│   │
│   ├── templatetags/            # Custom template tags
│   │   └── custom_filters.py    # Custom template filters
│   │
│   └── migrations/              # Database migrations
│       ├── 0001_initial.py
│       ├── 0002_alter_score_score.py
│       ├── 0003_archer_created_at_archer_updated_at_and_more.py
│       └── 0004_archer_club_name.py
│
├── capstone/                    # Project configuration
│   ├── settings.py              # Django settings
│   ├── urls.py                  # Root URL configuration
│   ├── wsgi.py                  # WSGI entry point
│   └── asgi.py                  # ASGI entry point
│
└── santi/                       # Additional settings (likely local)
    └── settings.py
```

---

## Database Design

### Entity-Relationship Diagram

```
┌──────────────┐              ┌──────────────┐
│ Competition  │              │   Category   │
├──────────────┤              ├──────────────┤
│ id (PK)      │              │ id (PK)      │
│ name         │              │ name         │
│ description  │              │ code         │
│ event_date   │              │ created_at   │
│ location     │              │ updated_at   │
│ code         │              └──────┬───────┘
│ created_at   │                     │
│ updated_at   │                     │
└──────┬───────┘                     │
       │                             │
       │         ┌──────────────┐    │
       │         │    Archer    │    │
       │         ├──────────────┤    │
       │         │ id (PK)      │    │
       │         │ name         │    │
       │         │ club_name    │    │
       │         │ email        │    │
       │         │ created_at   │    │
       │         │ updated_at   │    │
       │         └──────┬───────┘    │
       │                │            │
       │                │            │
       └────────────────┼────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  Registration    │
              ├──────────────────┤
              │ id (PK)          │
              │ competition_id(FK)│
              │ category_id (FK) │
              │ archer_id (FK)   │
              │ created_at       │
              │ updated_at       │
              └────────┬─────────┘
                       │
                       │
                       ▼
                ┌──────────────┐
                │    Score     │
                ├──────────────┤
                │ id (PK)      │
                │registration_id│
                │ score        │  ← CharField: "0"-"10","X","M"
                │ end_number   │  ← 1-12 (6 per round)
                │ shoot_number │  ← 1-6 (per end)
                │ created_at   │
                │ updated_at   │
                └──────────────┘
```

### Model Details

#### 1. Competition
**Purpose**: Represents an archery tournament event

| Field | Type | Description |
|-------|------|-------------|
| name | CharField(200) | Tournament name |
| description | CharField(300) | Event description |
| event_date | DateTimeField | When the tournament occurs |
| location | CharField(200) | Venue location |
| code | CharField(100) | Unique identifier/shortcode |
| created_at | DateTimeField | Auto-generated |
| updated_at | DateTimeField | Auto-updated |

**String Representation**: `"{name} | {code}"`

#### 2. Category
**Purpose**: Defines competition divisions (e.g., "Men's Recurve", "Women's Compound")

| Field | Type | Description |
|-------|------|-------------|
| name | CharField(200) | Category name |
| code | CharField(100) | Shortcode |
| created_at | DateTimeField | Auto-generated |
| updated_at | DateTimeField | Auto-updated |

**String Representation**: `"{name} | {code}"`

#### 3. Archer
**Purpose**: Stores participant information

| Field | Type | Description |
|-------|------|-------------|
| name | CharField(200) | Archer's full name |
| club_name | CharField(200) | Club affiliation |
| email | CharField(300) | Contact email |
| created_at | DateTimeField | Auto-generated |
| updated_at | DateTimeField | Auto-updated |

**String Representation**: `"{name} | {email}"`

**Note**: Added in migration 0004 - club_name field

#### 4. Registration
**Purpose**: Links archers to competitions and categories (M:M relationship table)

| Field | Type | Description |
|-------|------|-------------|
| competition | ForeignKey | → Competition (CASCADE) |
| category | ForeignKey | → Category (CASCADE) |
| archer | ForeignKey | → Archer (CASCADE) |
| created_at | DateTimeField | Auto-generated |
| updated_at | DateTimeField | Auto-updated |

**String Representation**: `"{competition.name} | {category.name} | {archer.name}"`

**Business Rule**: One archer can participate in multiple categories within a competition

#### 5. Score
**Purpose**: Stores individual arrow scores

| Field | Type | Description |
|-------|------|-------------|
| registration | ForeignKey | → Registration (CASCADE) |
| score | CharField(10) | "0"-"10", "X" (center 10), "M" (miss) |
| end_number | IntegerField | 1-12 (6 ends per round, 2 rounds) |
| shoot_number | IntegerField | 1-6 (6 arrows per end) |
| created_at | DateTimeField | Auto-generated |
| updated_at | DateTimeField | Auto-updated |

**String Representation**: `"{registration.archer.name} | {end_number} | {shoot_number} | {score}"`

**Scoring Logic**:
- **X**: 10 points + counts as both 10 and X for tiebreakers
- **10**: 10 points + counts as 10
- **M**: 0 points (miss)
- **1-9**: Face value

**Migration History**:
- 0002: Changed score field type (likely to CharField for X/M support)

### Database Relationships

1. **Competition ← Registration → Archer**: Many-to-Many through Registration
2. **Category ← Registration → Archer**: Many-to-Many through Registration
3. **Registration → Score**: One-to-Many (one registration has many scores)

### Data Integrity

**Cascade Deletions**:
- Deleting a Competition removes all Registrations and their Scores
- Deleting an Archer removes all their Registrations and Scores
- Deleting a Registration removes all associated Scores

**Constraints**:
- No unique constraints on Registration (archer can register multiple times?)
- No validation on end_number (should be 1-12)
- No validation on shoot_number (should be 1-6)

---

## Features Deep Dive

### 1. Competition Management

#### Admin Interface
**Access**: Django Admin (`/admin`)

**Capabilities**:
- Create/edit/delete Competitions
- Create/edit/delete Categories
- Create/edit/delete Archers
- Create Registrations (archer + category + competition)
- View all Scores

**Workflow**:
1. Admin creates Competition with metadata
2. Admin defines Categories for the competition
3. Admin adds Archers to database
4. Admin creates Registrations linking archers to categories

**Limitations**:
- No bulk registration import
- No validation of duplicate registrations
- No competition cloning feature

### 2. Scoring System (compete.html + compete.js)

#### User Interface Flow

**Step 1: Category Selection**
```
[Select Category Dropdown]
    ↓
[Displays multi-select of registered archers]
    ↓
[User selects participating archers]
```

**Step 2: Archer Scoring Interface**
```
[Archer Button Picker]
  Archer 1 | Archer 2 | Archer 3 ...
           ↓ (click)
[Scoring Form for Selected Archer]
  End 1:  [  ][  ][  ][  ][  ][  ]  Partial: 0  Total: 0  10s: 0  Xs: 0
          ↓ (fill scores)
  End 1:  [8][9][10][X][M][7]  Partial: 44  Total: 44  10s: 2  Xs: 1
          [Submit End 1] ← appears when all 6 arrows scored
           ↓
  End 2:  [  ][  ][  ][  ][  ][  ]  Partial: 0  Total: 44  10s: 0  Xs: 0
```

**Step 3: Score Persistence**
- Clicking "Submit End X" triggers `save_score_db()` AJAX call
- Scores saved to database with end_number and shoot_number
- Inputs become disabled after submission
- Next end automatically appears

#### Virtual Keyboard Integration

**KioskBoard Configuration**:
- Custom key layout: `["6","7","8","9","10","X"] ["M","1","2","3","4","5"]`
- Theme: Light
- Auto-scroll: Enabled
- Real keyboard: Disabled (touch-screen only)
- Mobile keyboard: Disabled
- Animations: Fade (90ms)

**Purpose**: Touch-screen optimized for tablets/kiosks in competition settings

#### Score Validation & Calculation

**Input Processing** (`compete.js` lines 130-160):
```javascript
function check_score_transform(score, end_number, archer_id) {
    if (score == 10) {
        add_10s(end_number, archer_id);
    }
    if (score == "M") {
        score = 0;
    }
    if (score == 'X') {
        add_xs(end_number, archer_id);
        add_10s(end_number, archer_id);
        score = 10;
    }
    return parseInt(score);
}
```

**Real-time Calculations**:
1. **Partial Score**: Sum of current end's 6 arrows
2. **Total Score**: Cumulative score up to current end
3. **10s Count**: Tally of 10s and Xs (for tiebreakers)
4. **Xs Count**: Tally of Xs only (secondary tiebreaker)

**Final Totals**:
- Updated after each end submission
- Displayed prominently for each archer
- Used for results ranking

#### AJAX Endpoints

**`/add_archer_div`** (POST):
- **Input**: `{archer_id: int}`
- **Output**: HTML fragment with archer scoring container
- **Purpose**: Dynamically load scoring interface for selected archer

**`/add_score_div`** (POST):
- **Input**: `{end_number: int, archer_id: int}`
- **Output**: HTML fragment with 6 score inputs + stats
- **Purpose**: Add scoring row for next end

**`/save_score_db`** (POST):
- **Input**: `{shoot_array: [scores], archer_id: int, end_number: int, category_id: int}`
- **Output**: `{message: "Score saved successfully."}`
- **Logic**:
  - Fetches Registration from session + form data
  - Deletes existing scores for this end (allows re-scoring)
  - Creates 6 Score objects (one per arrow)
- **Error Handling**: Returns 400 on IntegrityError

#### Session Management

**`current_competition`** stored in session:
```python
competition_data = {
    'id': competition.id,
    'name': competition.name,
}
request.session['current_competition'] = json.dumps(competition_data)
```

**Purpose**: Persist selected competition across requests without URL parameters

### 3. Shoot Timer (shoot_timer.html + shoot_timer.js)

#### Timer Phases

**Phase 1: Preparation (10 seconds)**
- **Sound**: 2 beeps (whistle.wav)
- **Display**: Countdown from 00:10 to 00:00
- **Purpose**: Archers get into position

**Phase 2: Competition (3 minutes)**
- **Sound**: 1 beep (whistle.wav)
- **Display**: Countdown from 03:00 to 00:00
- **Warning**: 10-second warning sound (warning.mp3) at 00:10
- **Purpose**: Shooting time

**Phase 3: Finish**
- **Sound**: 3 beeps (whistle.wav)
- **Display**: "time's up"
- **Reset**: Returns to start state

#### State Machine

```javascript
let status = 'preparing'; // Global state

function countdown(element, minutes, seconds) {
    interval = setInterval(function() {
        if (time <= 0) {
            if (status == 'preparing') {
                clearInterval(interval);
                start_competition_timer();
                status = 'competing';
                return;
            }
            if (status == 'competing') {
                clearInterval(interval);
                status = 'preparing';
                finish_timer();
                return;
            }
        }
        // ... countdown logic
    }, 1000);
}
```

#### Audio Implementation

**Promise-based playback**:
```javascript
function playAudio(audio){
    return new Promise(res=>{
        audio.currentTime = 0; // Reset to start
        audio.play()
        audio.onended = res // Resolve when finished
    })
}

async function beep(){
    const audio = document.getElementById('beep_audio');
    await playAudio(audio)
}
```

**Benefits**:
- Sequential sound playback (2 beeps = `await beep(); await beep();`)
- Non-blocking countdown start
- Prevents overlapping sounds

#### Visual Design

**Clock Display**:
- Font: Orbitron (digital/futuristic)
- Size: Large (defined in styles.css)
- Format: MM:SS
- Visibility: Toggled based on timer state

**Controls**:
- Start Button: Green, large (`btn-success btn-lg`)
- Stop Button: Red, large (`btn-danger btn-lg`)
- Stop hidden initially, appears during countdown

### 4. Results Display (result_screen.html + results.js)

#### Display Logic

**Data Retrieval** (`/result_category` endpoint):
```python
def result_category(request):
    # Get all registrations for category in current competition
    registrations_archers = Registration.objects.filter(
        competition_id=competition_id, 
        category_id=category_id
    )
    
    # Calculate total score for each archer
    archer_list = []
    for registration in registrations_archers:
        scores = Score.objects.filter(registration_id=registration.id)
        score_sum = 0
        for score in scores:
            score_value = 0
            if score.score == 'X':
                score_value = 10
            elif score.score == 'M':
                score_value = 0
            else:
                score_value = int(score.score)
            score_sum += score_value
        archer_list.append({
            'name': archer.name,
            'score': score_sum
        })
    
    # Sort by score (descending)
    sorted_archer_list = sorted(archer_list, key=lambda x: x['score'], reverse=True)
    return JsonResponse({"data": json.dumps(sorted_archer_list)}, status=201)
```

**Ranking Display**:
```html
<div class="row justify-content-between mt-4">
    <h1 class="col-1">1</h1>          <!-- Rank -->
    <h1 class="col-9">Archer Name</h1> <!-- Name -->
    <h1 class="col-2">532</h1>         <!-- Score -->
</div>
```

#### Auto-Rotation Feature

**Implementation** (`results.js` lines 47-58):
```javascript
const options = select_category.options;
let index = 1;

function changeDropdownValue() {
    if (index < options.length) {
        select_category.selectedIndex = index;
        select_category.dispatchEvent(new Event('change'));
        index++;
    } else {
        index = 1; // Reset to first category
        select_category.selectedIndex = index;
        select_category.dispatchEvent(new Event('change'));
        index++;
    }
}
setInterval(changeDropdownValue, 3000); // Every 3 seconds
```

**User Experience**:
- Automatically cycles through all categories
- 3-second display per category
- Infinite loop
- Category selector visible (manual selection allowed)

**Use Case**: Large screen display for spectators in venue

#### Tiebreaker Support

**Current Implementation**: None

**Limitation**: Archers with same score receive same rank without differentiation by:
1. Number of 10s
2. Number of Xs
3. Last end score

**Database Support**: 10s and Xs ARE tracked in scoring interface but NOT stored in database

---

## Technical Implementation

### Frontend Architecture

#### Client-Side Processing Philosophy

**Design Decision**: Heavy client-side JavaScript processing

**Rationale** (from readme.md):
> "Ensuring that the system remained responsive and reliable under heavy load was a key consideration using mostly javascript that runs on the client for the procesing information and make calculations."

**Benefits**:
- Reduced server load
- Instant UI updates
- Offline-capable scoring (if modified)

**Drawbacks**:
- Duplicated logic (client + server validation)
- Increased bundle size (426 lines in compete.js)
- Harder to maintain consistency

#### State Management

**No Framework**: Pure DOM manipulation + fetch API

**State Storage**:
1. **Session**: `current_competition` stored server-side
2. **DOM**: Data attributes (`data-archer_id`, `data-end`, `data-shoot`)
3. **Variables**: Global `status` in shoot_timer.js

**Event Handling**:
```javascript
// Pattern used throughout
document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('#selector').addEventListener('event', handler);
    const divs = document.querySelectorAll('.class');
    divs.forEach(el => el.addEventListener('event', handler));
});
```

#### Dynamic HTML Injection

**Pattern**: Server returns HTML fragments, client injects via `insertAdjacentHTML`

**Example**:
```javascript
fetch(`/add_archer_div`, {
    method: 'POST',
    body: JSON.stringify({ archer_id: archer_id })
})
.then(response => response.text())
.then(result => {
    document.querySelector('#archers_container').insertAdjacentHTML(
        'beforeend',
        result
    );
    // Re-attach event listeners to new HTML
    const divs = document.querySelectorAll(`.archer_picker`);
    divs.forEach(el => el.addEventListener('click', change_archer));
})
```

**Risk**: XSS vulnerability if user input not sanitized in templates

### Backend Architecture

#### View Organization

**View Count**: 10 views in views.py (165 lines)

**Categories**:
1. **Page Views**: `index`, `competitions`, `select_competition`, `compete`, `result_screen`, `shoot_timer`
2. **AJAX Endpoints**: `add_score_div`, `add_archer_div`, `save_score_db`, `result_category`

**Authentication**: None (all views unprotected)

**CSRF Protection**: 
- Enabled globally
- Disabled on AJAX endpoints with `@csrf_exempt`
- **Security Risk**: Vulnerable to CSRF attacks on scoring/results

#### Data Access Patterns

**Inefficient N+1 Queries** (compete view):
```python
registrations = Registration.objects.filter(competition=competition)
categories_map = defaultdict(list)
for registration in registrations:
    # N+1: Queries archer for each registration
    categories_map[registration.category_id].append(registration.archer)
```

**Better Approach**:
```python
registrations = Registration.objects.filter(
    competition=competition
).select_related('archer', 'category')
```

**Inefficient Score Calculation** (result_category view):
```python
for registration in registrations_archers:
    # Query all scores for each archer
    scores = Score.objects.filter(registration_id=registration.id)
    # Loop through all scores
    for score in scores:
        score_sum += score_value
```

**Better Approach**: Use aggregation:
```python
from django.db.models import Sum, Case, When, IntegerField

registrations = Registration.objects.filter(
    competition_id=competition_id,
    category_id=category_id
).annotate(
    total_score=Sum(
        Case(
            When(score__score='X', then=10),
            When(score__score='M', then=0),
            default='score__score',
            output_field=IntegerField()
        )
    )
).order_by('-total_score')
```

#### Template Rendering

**Base Template** (layout.html):
- Bootstrap 4 navbar
- CDN dependencies (jQuery, Popper, Bootstrap)
- Static CSS/JS loading
- Blocks: `title`, `content`, `scripts`

**Template Inheritance**:
```
layout.html
  ├── home.html
  ├── competitions.html
  ├── competition.html (hub page)
  ├── compete.html
  ├── shoot_timer.html
  └── result_screen.html
```

**Partial Templates** (AJAX responses):
- `archer_div.html`: Scoring container for one archer
- `score_div.html`: Score input row for one end

### Static Assets

**CSS**:
- Bootstrap 4.5.0 (CDN)
- Bootstrap Icons (CDN)
- Google Fonts Orbitron (CDN)
- `styles.css` (custom styles)
- `kioskboard-2.3.0.min.css`

**JavaScript**:
- jQuery 3.5.1 (CDN)
- Popper.js 1.16.0 (CDN)
- Bootstrap 4.5.0 (CDN)
- `compete.js` (426 lines)
- `shoot_timer.js` (98 lines)
- `results.js` (95 lines)
- `kioskboard-2.3.0.min.js`

**Audio**:
- `whistle.wav`: Timer start/end beeps
- `warning.mp3`: 10-second warning

**Total Bundle Size**: Not optimized (multiple CDN requests + large JS files)

### URL Routing

**URL Pattern** (`artemisa/urls.py`):
```python
urlpatterns = [
    path("", views.index, name="index"),
    path("competitions", views.competitions, name="competitions"),
    path("select_competition/<int:competition_id>", views.select_competition, name="select_competition"),
    path("compete/<int:competition_id>", views.compete, name="compete"),
    path("add_score_div", views.add_score_div, name="add_score_div"),
    path("add_archer_div", views.add_archer_div, name="add_archer_div"),
    path("save_score_db", views.save_score_db, name="save_score_db"),
    path("result_screen/<int:competition_id>", views.result_screen, name="result_screen"),
    path("result_category", views.result_category, name="result_category"),
    path("shoot_timer/<int:competition_id>", views.shoot_timer, name="shoot_timer"),
]
```

**Root URLs** (`capstone/urls.py`):
```python
# Not visible in provided context, likely:
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('artemisa.urls')),
]
```

---

## User Workflows

### Workflow 1: Setting Up a Tournament (Admin)

**Prerequisites**: Superuser account created

1. **Access Admin**:
   - Navigate to `/admin`
   - Login with superuser credentials

2. **Create Competition**:
   - Click "Competitions" → "Add Competition"
   - Fill in:
     - Name: "National Championship 2026"
     - Description: "Annual national tournament"
     - Event Date: 2026-03-15 10:00
     - Location: "National Sports Center"
     - Code: "NAT2026"
   - Save

3. **Define Categories**:
   - Click "Categories" → "Add Category"
   - Create multiple categories:
     - Men's Recurve (code: MR)
     - Women's Recurve (code: WR)
     - Men's Compound (code: MC)
     - Women's Compound (code: WC)

4. **Add Archers**:
   - Click "Archers" → "Add Archer"
   - For each participant:
     - Name: "John Doe"
     - Club Name: "City Archery Club"
     - Email: "john@example.com"
   - Save

5. **Register Archers**:
   - Click "Registrations" → "Add Registration"
   - Select:
     - Competition: National Championship 2026
     - Category: Men's Recurve
     - Archer: John Doe
   - Save
   - Repeat for all archer-category combinations

6. **Verify Setup**:
   - Navigate to `/competitions`
   - Click on competition
   - Verify categories and archers appear correctly

**Time Estimate**: 15-30 minutes for 50 archers across 4 categories

### Workflow 2: Scoring During Competition (Judge/Operator)

**Prerequisites**: Competition setup complete, device with large touch screen

1. **Select Competition**:
   - Navigate to `/competitions`
   - Click on active competition
   - Lands on competition hub page

2. **Open Scoring Interface**:
   - Click "Scoreboard" button
   - Opens `/compete/<competition_id>`

3. **Select Category**:
   - From dropdown, select "Men's Recurve"
   - Multi-select appears with registered archers

4. **Select Competing Archers** (for current detail):
   - Multi-select archers currently shooting:
     - John Doe
     - Jane Smith
     - Bob Johnson
   - Click outside to confirm

5. **Score First Archer**:
   - Archer button bar appears:
     ```
     [John Doe] [Jane Smith] [Bob Johnson]
     ```
   - Click "John Doe" button (highlights, becomes active)
   - Scoring form appears:
     ```
     End 1: [  ][  ][  ][  ][  ][  ]  Partial: 0  Total: 0  10s: 0  Xs: 0
     ```

6. **Enter Scores**:
   - Click first input (virtual keyboard appears)
   - Enter arrow scores: 10, 9, X, 9, 10, 8
   - After each entry:
     - Partial updates: 10 → 19 → 29 → 38 → 48 → 56
     - Counters update: 10s: 3, Xs: 1
     - Auto-focus moves to next input

7. **Submit End**:
   - "Submit End 1" button appears when all 6 scores entered
   - Click button:
     - Scores saved to database
     - Inputs become disabled
     - End 2 form appears automatically
     - Final totals update

8. **Continue Scoring**:
   - Switch between archers using button bar
   - Each archer can be at different end
   - Complete ends 1-6 (Round 1), then 7-12 (Round 2)

9. **Handle Corrections**:
   - If error noticed before submitting end:
     - Click incorrect input
     - Re-enter correct score
     - Totals recalculate automatically
   - If error noticed after submitting:
     - **Current System**: Cannot edit (limitation)
     - **Workaround**: Admin must manually fix in database

**Time Estimate**: 2-3 minutes per archer per end (with 6 arrows)

### Workflow 3: Timer Operation (Judge)

**Prerequisites**: Competition in progress, audio enabled

1. **Access Timer**:
   - From competition hub, click "Shoot Timer"
   - Opens `/shoot_timer/<competition_id>`

2. **Start Sequence**:
   - Click green "Start" button
   - **Preparation Phase Begins**:
     - 2 whistles sound
     - Clock appears showing 00:10
     - Countdown begins: 00:09 → 00:08 → ...
     - Archers take positions

3. **Competition Phase Transition**:
   - At 00:00, automatic transition:
     - 1 whistle sounds
     - Clock resets to 03:00
     - Countdown begins: 02:59 → 02:58 → ...
     - Archers shoot

4. **10-Second Warning**:
   - At 00:10 remaining:
     - Warning sound plays (distinct from whistle)
     - Archers prepare to finish

5. **End of Shooting**:
   - At 00:00:
     - 3 whistles sound
     - "time's up" message displays
     - Clock disappears
     - Green "Start" button reappears

6. **Emergency Stop**:
   - If needed (safety issue), click red "Stop" button:
     - Timer stops immediately
     - 3 whistles sound
     - Resets to start state

7. **Repeat**:
   - Click "Start" again for next detail

**Time Estimate**: 3:10 per shooting detail (10s prep + 3:00 competition)

### Workflow 4: Results Display (Spectators)

**Prerequisites**: Scores entered for at least one category

1. **Access Results**:
   - From competition hub, click "Results Screen"
   - Opens `/result_screen/<competition_id>`
   - **Display Mode**: Fullscreen on large TV/projector

2. **Automatic Display**:
   - Category selector auto-changes every 3 seconds
   - First category loads:
     ```
     Results - National Championship 2026
     Category: Men's Recurve
     
     1    John Doe        532
     2    Bob Johnson     528
     3    Jane Smith      520
     ```
   - After 3 seconds, switches to next category:
     ```
     Results - National Championship 2026
     Category: Women's Recurve
     
     1    Alice Cooper    545
     2    Mary Jane       540
     ...
     ```

3. **Manual Control** (if needed):
   - Click category dropdown
   - Select specific category
   - Auto-rotation continues from that point

4. **Real-Time Updates**:
   - Refresh page to see latest scores
   - **No Auto-Refresh**: Must manually reload

**Use Case**: Continuous display in venue lobby or competition area

---

## Security Considerations

### Critical Vulnerabilities

#### 1. No Authentication

**Issue**: All views are unprotected
```python
# No @login_required decorators
def compete(request, competition_id):
    # Anyone can access scoring
```

**Impact**:
- Anyone can score competitions
- Anyone can view/modify results
- No audit trail of who scored what

**Recommendation**: Implement Django authentication:
```python
from django.contrib.auth.decorators import login_required, permission_required

@login_required
@permission_required('artemisa.can_score_competition', raise_exception=True)
def compete(request, competition_id):
    ...
```

#### 2. CSRF Protection Disabled on AJAX

**Issue**:
```python
@csrf_exempt
def add_score_div(request):
    ...

@csrf_exempt
def save_score_db(request):
    ...
```

**Impact**: 
- Scoring endpoints vulnerable to CSRF attacks
- Attacker can submit fake scores from malicious site

**Fix**: Use CSRF tokens properly:
```javascript
// In HTML template
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

// In JavaScript
fetch('/save_score_db', {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
})
```

#### 3. Database Credentials in Settings

**Issue** (settings.py):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'artemisa',
        'USER': 'artemisa',
        'PASSWORD': 'REDACTED',  # ← a real value was committed here once; removed from history 2026-11-14
        'HOST': 'localhost',
        'PORT': '',
    }
}
```

**Impact**: Password visible in version control

**Fix**: Use environment variables:
```python
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME', 'artemisa'),
        'USER': os.environ.get('DB_USER', 'artemisa'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

#### 4. DEBUG = True in Settings

**Issue**:
```python
DEBUG = True
```

**Impact**:
- Exposes stack traces with sensitive info
- Shows SQL queries in error pages
- Disables certain security features

**Fix**: Set to False in production, use environment variable

#### 5. SECRET_KEY in Settings

**Issue**:
```python
SECRET_KEY = "REDACTED"
```

**Impact**: Compromised session security, CSRF tokens, password reset tokens

**Fix**: Move to environment variable, rotate key

### Additional Security Issues

#### 6. SQL Injection (Low Risk)

**Status**: Protected by Django ORM

**Caveat**: If raw SQL added later, risk increases

#### 7. XSS (Cross-Site Scripting)

**Risk Level**: Medium

**Vulnerable Areas**:
- Archer names rendered in templates without escaping
- Dynamic HTML injection in JavaScript

**Django Protection**: Auto-escapes template variables

**JavaScript Risk**:
```javascript
result_container.insertAdjacentHTML(
    'beforeend',
    `<h1>${archer.name}</h1>`  // ← If name contains <script>, executes
);
```

**Fix**: Sanitize or use textContent:
```javascript
const div = document.createElement('div');
div.textContent = archer.name;  // Auto-escapes
result_container.appendChild(div);
```

#### 8. Input Validation

**Issue**: Minimal server-side validation

**Examples**:
- No validation that end_number is 1-12
- No validation that shoot_number is 1-6
- No validation that score is valid archery score
- No uniqueness check on Registration

**Client-Side Validation**: Present but bypassable

**Fix**: Add Django model validation:
```python
from django.core.validators import MinValueValidator, MaxValueValidator

class Score(models.Model):
    score = models.CharField(max_length=10, validators=[validate_archery_score])
    end_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    shoot_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)]
    )
```

---

## Improvements and Recommendations

### High Priority (Critical)

#### 1. Implement Authentication & Authorization

**Problem**: No access control

**Solution**:
- Add Django authentication
- Create user roles:
  - **Admin**: Full access
  - **Judge**: Scoring + timer
  - **Viewer**: Results only
- Add `@login_required` to all views
- Implement permission checks

**Effort**: 2-3 days

**Impact**: Eliminates major security vulnerability

#### 2. Fix CSRF Protection

**Problem**: CSRF disabled on critical endpoints

**Solution**:
- Remove `@csrf_exempt` decorators
- Implement proper CSRF token handling in AJAX
- Use Django's built-in CSRF middleware

**Effort**: 4 hours

**Impact**: Prevents score manipulation attacks

#### 3. Move Secrets to Environment Variables

**Problem**: Credentials in version control

**Solution**:
- Use python-decouple or django-environ
- Create `.env` file (add to .gitignore)
- Update settings.py to read from environment
- Rotate all exposed secrets

**Effort**: 2 hours

**Impact**: Prevents credential leaks

#### 4. Add Tiebreaker Logic

**Problem**: Archers with same score have no differentiation

**Solution**:
- Store 10s and Xs counts in Score model or as aggregates
- Modify result_category view to:
  1. Sort by total score
  2. Then by 10s count
  3. Then by Xs count
  4. Then by last end score
- Update results.js to display tiebreakers

**Effort**: 1 day

**Impact**: Correct competitive rankings

#### 5. Optimize Database Queries

**Problem**: N+1 queries causing performance issues

**Solution**:
- Use `select_related()` for foreign keys
- Use `prefetch_related()` for reverse relationships
- Implement aggregation for score calculations
- Add database indexes on frequently queried fields

**Example**:
```python
# Before (N+1)
registrations = Registration.objects.filter(competition=competition)
for registration in registrations:
    archer = registration.archer  # ← Separate query

# After (1 query)
registrations = Registration.objects.filter(
    competition=competition
).select_related('archer', 'category')
```

**Effort**: 1 day

**Impact**: 10-100x performance improvement on large tournaments

### Medium Priority (Important)

#### 6. Add Score Editing Capability

**Problem**: Cannot fix score errors after submission

**Solution**:
- Add "Edit End" button that re-enables inputs
- Track edit history for audit trail
- Require authentication before editing
- Show "edited" indicator on modified ends

**Effort**: 2 days

**Impact**: Reduces admin burden, improves accuracy

#### 7. Implement Real-Time Updates (WebSockets)

**Problem**: Results screen requires manual refresh

**Solution**:
- Add Django Channels for WebSocket support
- Broadcast score updates to results screen
- Auto-update leaderboard without refresh
- Show "LIVE" indicator when connected

**Effort**: 3-4 days

**Impact**: Better spectator experience

#### 8. Add Bulk Registration Import

**Problem**: Tedious to register many archers via admin

**Solution**:
- Create CSV import view
- Format: `archer_name, archer_email, club_name, category_code`
- Validate before import
- Show preview before committing

**Effort**: 2 days

**Impact**: Reduces setup time for large tournaments

#### 9. Add Competition Cloning

**Problem**: Must recreate recurring tournaments

**Solution**:
- Add "Clone Competition" button in admin
- Copy competition metadata
- Optionally copy registrations
- Update event_date and code

**Effort**: 1 day

**Impact**: Faster setup for annual events

#### 10. Improve Error Handling

**Problem**: Minimal error feedback to users

**Solution**:
- Add try-catch blocks in JavaScript
- Show user-friendly error messages
- Log errors to console or server
- Add rollbar or sentry for error tracking

**Example**:
```javascript
fetch('/save_score_db', { ... })
.then(response => {
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
})
.catch(error => {
    alert('Failed to save score. Please try again.');
    console.error('Score save error:', error);
});
```

**Effort**: 1 day

**Impact**: Better debugging and user experience

### Low Priority (Nice to Have)

#### 11. Add Unit Tests

**Problem**: No test coverage (tests.py empty)

**Solution**:
- Write model tests (validation, relationships)
- Write view tests (responses, calculations)
- Write integration tests (end-to-end workflows)
- Aim for 80%+ coverage

**Example**:
```python
from django.test import TestCase

class ScoreModelTest(TestCase):
    def test_x_counts_as_10(self):
        score = Score.objects.create(
            registration=self.registration,
            score='X',
            end_number=1,
            shoot_number=1
        )
        self.assertEqual(score.numeric_value(), 10)
```

**Effort**: 1 week

**Impact**: Prevents regressions, enables refactoring

#### 12. Add API for Mobile Apps

**Problem**: Only web interface available

**Solution**:
- Add Django REST Framework
- Create API endpoints:
  - `/api/competitions/` (list)
  - `/api/competitions/<id>/scores/` (get/post)
  - `/api/competitions/<id>/results/` (get)
- Add JWT authentication
- Document with Swagger/OpenAPI

**Effort**: 1 week

**Impact**: Enables native mobile apps, third-party integrations

#### 13. Add Reporting & Statistics

**Problem**: No historical analysis

**Solution**:
- Add reports view:
  - Archer performance over time
  - Category averages
  - Competition summaries
- Export to PDF/Excel
- Add charts (Chart.js or Plotly)

**Effort**: 1 week

**Impact**: Better insights for archers and organizers

#### 14. Add Internationalization (i18n)

**Problem**: English only

**Solution**:
- Use Django's i18n framework
- Translate templates and messages
- Add language selector
- Support common archery languages (Spanish, French, German, Korean)

**Effort**: 3-4 days

**Impact**: Broader adoption in international tournaments

#### 15. Add Email Notifications

**Problem**: No communication with archers

**Solution**:
- Send registration confirmations
- Send schedule reminders
- Send results after competition
- Use Celery for async sending

**Effort**: 2 days

**Impact**: Better communication and engagement

#### 16. Add PWA (Progressive Web App) Features

**Problem**: No offline capability

**Solution**:
- Add service worker
- Cache static assets
- Enable offline scoring (sync when online)
- Add "Add to Home Screen" prompt

**Effort**: 3-4 days

**Impact**: Works in poor connectivity, feels like native app

#### 17. Improve UI/UX Design

**Problem**: Basic Bootstrap styling

**Solution**:
- Hire designer or use modern template
- Add consistent color scheme
- Improve mobile responsiveness
- Add loading indicators
- Add animations and transitions
- Improve form validation feedback

**Effort**: 1 week

**Impact**: More professional appearance

#### 18. Add Archery-Specific Validations

**Problem**: System accepts any scores

**Solution**:
- Validate based on competition type:
  - Target archery: 1-10, X, M
  - Field archery: Different scoring
  - 3D archery: Different targets
- Add distance and target size settings
- Validate score plausibility (e.g., flag if all Xs)

**Effort**: 2-3 days

**Impact**: Data integrity, sport accuracy

#### 19. Add Multi-Tournament Support

**Problem**: One instance = one tournament

**Solution**:
- Add organization/club model
- Multi-tenancy (one instance, many clubs)
- Separate data by organization
- Add subscription model for commercial use

**Effort**: 1-2 weeks

**Impact**: SaaS business model possible

#### 20. Add Backup & Recovery

**Problem**: No backup strategy

**Solution**:
- Add automated database backups
- Implement backup to cloud storage (S3, GCS)
- Add restore functionality
- Document disaster recovery process

**Effort**: 2 days

**Impact**: Data safety and business continuity

---

## Performance Optimization

### Database Optimization

**Current Issues**:
1. N+1 queries in compete and result_category views
2. No database indexes on foreign keys
3. Inefficient score aggregation

**Solutions**:
```python
# Add indexes
class Score(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, db_index=True)
    end_number = models.IntegerField(default=0, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['registration', 'end_number']),
        ]
```

### Frontend Optimization

**Current Issues**:
1. Multiple CDN requests (6+ external resources)
2. Large JavaScript files (426 lines compete.js)
3. No code minification
4. No lazy loading

**Solutions**:
- Bundle JavaScript files
- Minify CSS and JS
- Use webpack or vite for build process
- Lazy load results (pagination instead of all at once)
- Add browser caching headers

### Caching Strategy

**Opportunities**:
1. Cache category list (rarely changes)
2. Cache archer lists per competition
3. Cache results (invalidate on new scores)

**Implementation**:
```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # Cache for 5 minutes
def result_category(request):
    ...
```

---

## Deployment Considerations

### Current Deployment

**Server**: Gunicorn WSGI server

**Domain**: artemisa.lajota.com.py

**Environment**: Production (despite DEBUG=True)

### Recommended Production Setup

**Architecture**:
```
Internet
   ↓
Nginx (Reverse Proxy, SSL Termination)
   ↓
Gunicorn (WSGI Server, multiple workers)
   ↓
Django Application
   ↓
PostgreSQL Database
```

**Configuration**:

**Nginx** (`/etc/nginx/sites-available/artemisa`):
```nginx
server {
    listen 80;
    server_name artemisa.lajota.com.py;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name artemisa.lajota.com.py;

    ssl_certificate /etc/letsencrypt/live/artemisa.lajota.com.py/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/artemisa.lajota.com.py/privkey.pem;

    location /static/ {
        alias /path/to/artemisa/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Gunicorn** (systemd service):
```ini
[Unit]
Description=Artemisa Gunicorn Daemon
After=network.target

[Service]
User=artemisa
Group=www-data
WorkingDirectory=/path/to/artemisa
Environment="PATH=/path/to/artemisa/aremisaenv/bin"
ExecStart=/path/to/artemisa/aremisaenv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/artemisa/access.log \
    --error-logfile /var/log/artemisa/error.log \
    capstone.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Settings** (production.py):
```python
DEBUG = False
ALLOWED_HOSTS = ['artemisa.lajota.com.py']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### Monitoring

**Tools**:
- Sentry: Error tracking
- New Relic / DataDog: Performance monitoring
- Uptime Robot: Availability monitoring
- PostgreSQL logs: Database performance

### Backup Strategy

**Database**:
```bash
# Daily backups
pg_dump artemisa > backup_$(date +%Y%m%d).sql

# Upload to S3
aws s3 cp backup_$(date +%Y%m%d).sql s3://artemisa-backups/
```

**Files**:
- Static files: Regenerable, low priority
- Media files: None in current system

---

## Conclusion

### Project Strengths

1. **Domain Expertise**: Purpose-built for archery with sport-specific features
2. **User Experience**: Intuitive interfaces for judges and spectators
3. **Real-Time Capabilities**: Timer and scoring updates
4. **Touch Optimization**: Virtual keyboard for tablets
5. **Simplicity**: No complex dependencies, easy to understand

### Critical Weaknesses

1. **Security**: No authentication, CSRF disabled, exposed credentials
2. **Performance**: N+1 queries, no caching, inefficient aggregations
3. **Data Integrity**: Missing validations, no tiebreaker support
4. **Maintainability**: No tests, duplicated logic, no documentation
5. **Scalability**: Single instance, no API, no multi-tenancy

### Immediate Actions Required

1. **Security Hardening** (1 week):
   - Implement authentication
   - Fix CSRF protection
   - Move secrets to environment variables
   - Set DEBUG=False
   - Rotate exposed credentials

2. **Performance Optimization** (3 days):
   - Fix N+1 queries
   - Add database indexes
   - Implement query optimization
   - Add basic caching

3. **Data Integrity** (2 days):
   - Add model validations
   - Implement tiebreaker logic
   - Add uniqueness constraints

### Long-Term Vision

**Phase 1: Stabilization** (1 month)
- Fix security issues
- Add tests
- Optimize performance
- Add score editing

**Phase 2: Enhancement** (2 months)
- Real-time updates (WebSockets)
- Bulk import
- API development
- Mobile app

**Phase 3: Scale** (3+ months)
- Multi-tenancy
- Advanced reporting
- Email notifications
- International support
- SaaS offering

### Final Assessment

Artemisa is a **functional and innovative** archery scoring system with strong domain-specific features and user experience. However, it suffers from **critical security vulnerabilities** and **performance issues** that must be addressed before production use at scale.

With focused effort on security hardening, performance optimization, and feature completion (especially tiebreakers), Artemisa could become a **robust and competitive** solution in the archery tournament management space.

**Current State**: Beta / Prototype
**Production Ready**: No (security issues)
**Market Potential**: High (niche market with specific needs)
**Technical Debt**: Moderate to High
**Recommended Investment**: 2-3 months of development to reach production quality

---

**Document Version**: 1.0  
**Date**: January 23, 2026  
**Author**: Technical Analysis  
**Pages**: 47
