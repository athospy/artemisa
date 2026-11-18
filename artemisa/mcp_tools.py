"""Read-only tools exposed by the MCP server (`python manage.py mcp`).

Plain functions so they can be tested without an MCP client. Each one only reads
the database; none of them calls the Anthropic API. Archer emails are never returned.
"""
from collections import defaultdict

from django.db.models import Count
from mcp.server.mcpserver.exceptions import ToolError

from . import recap, standings
from .models import Competition, Registration, Score


def _competition(competition_id):
    competition = Competition.objects.filter(pk=competition_id).first()
    if competition is None:
        raise ToolError(f"No competition with id {competition_id}. Use list_competitions to see the ids.")
    return competition


def list_competitions():
    """Every competition, newest first, with its categories and archer counts."""
    result = []
    for competition in Competition.objects.order_by('-event_date'):
        categories = (
            Registration.objects.filter(competition=competition)
            .values('category__name', 'category__code')
            .annotate(archers=Count('id'))
            .order_by('category__name')
        )
        result.append({
            'id': competition.id,
            'name': competition.name,
            'date': competition.event_date.date().isoformat(),
            'location': competition.location,
            'is_demo': competition.is_demo,
            'categories': [
                {'name': c['category__name'], 'code': c['category__code'], 'archers': c['archers']}
                for c in categories
            ],
        })
    return result


def get_leaderboard(competition_id, category=None):
    """Ranked archers per category. `category` (name or code, any case) limits it to one."""
    competition = _competition(competition_id)
    categories = standings.competition_standings(competition)
    if category:
        wanted = category.strip().lower()
        categories = [c for c in categories if wanted in (c['category'].lower(), c['code'].lower())]
        if not categories:
            raise ToolError(f"No category '{category}' in competition {competition_id}.")
    return {
        'competition': competition.name,
        'categories': [
            {
                'category': c['category'],
                'code': c['code'],
                'ranking': [
                    {'rank': rank, **{k: a[k] for k in ('name', 'club', 'score', 'tens', 'xs', 'last_end_total')}}
                    for rank, a in enumerate(c['archers'], start=1)
                ],
            }
            for c in categories
        ],
    }


def get_archer_scorecard(competition_id, archer_name):
    """End-by-end arrows for one archer, found by (part of) their name."""
    competition = _competition(competition_id)
    registrations = list(
        Registration.objects.filter(competition=competition, archer__name__icontains=archer_name.strip())
        .select_related('archer', 'category')
        .order_by('archer__name', 'category__name')
    )
    archers = {r.archer.name for r in registrations}
    if not archers:
        raise ToolError(f"No archer matching '{archer_name}' in competition {competition_id}.")
    if len(archers) > 1:
        raise ToolError(f"'{archer_name}' matches several archers: {', '.join(sorted(archers))}. Use a fuller name.")

    scorecards = []
    for registration in registrations:  # one per category the archer shot in
        ends = defaultdict(list)
        for score in Score.objects.filter(registration=registration).order_by('end_number', 'shoot_number'):
            ends[score.end_number].append(score.score)
        ranking = standings.category_ranking(competition.id, registration.category_id)
        rank = next(i for i, a in enumerate(ranking, start=1) if a['archer_id'] == registration.archer_id)
        running_total = 0
        end_rows = []
        for end_number, arrows in sorted(ends.items()):
            end_total = sum(_arrow_points(a) for a in arrows)
            running_total += end_total
            end_rows.append({'end': end_number, 'arrows': arrows, 'end_total': end_total, 'running_total': running_total})
        scorecards.append({
            'category': registration.category.name,
            'rank': rank,
            'of': len(ranking),
            'total': running_total,
            'ends': end_rows,
        })
    archer = registrations[0].archer
    return {'competition': competition.name, 'archer': archer.name, 'club': archer.club_name, 'scorecards': scorecards}


def get_match_recap(competition_id):
    """The saved AI recap, if it was written from the current standings. Never calls the API."""
    competition = _competition(competition_id)
    text = recap.saved_recap(competition, recap.recap_input(competition))
    return {
        'competition': competition.name,
        'recap': text or None,
        'note': None if text else "No saved recap for the current standings. One is written from the web app's recap page.",
    }


def _arrow_points(arrow):
    return 10 if arrow == 'X' else 0 if arrow == 'M' else int(arrow)
