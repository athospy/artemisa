"""Rankings: one place for the scoring rules and the tiebreaker chain.

Used by the results screen (views.result_category), the AI recap (recap.py) and the
MCP server (management/commands/mcp.py).

Scoring: X counts 10 points and also counts as an X; M (miss) counts 0.
Ties: total points, then number of 10s (X included), then number of Xs, then the
points in the archer's last end; archer name only makes the order stable.
"""
from django.db.models import Case, F, IntegerField, OuterRef, Subquery, Sum, Value, When
from django.db.models.functions import Cast, Coalesce

from .models import Category, Registration, Score


def _points(field):
    """SQL expression for the points of one arrow stored in `field`."""
    return Case(
        When(**{field: 'X'}, then=Value(10)),
        When(**{field: 'M'}, then=Value(0)),
        default=Cast(F(field), IntegerField()),
        output_field=IntegerField(),
    )


def _count(**condition):
    return Coalesce(Sum(Case(When(**condition, then=Value(1)), default=Value(0), output_field=IntegerField())), Value(0))


def category_ranking(competition_id, category_id):
    """Ranked archers of one category in one competition, best first."""
    last_end_total = Subquery(
        Score.objects.filter(registration=OuterRef('pk'))
        .values('end_number')
        .annotate(end_total=Sum(_points('score')))
        .order_by('-end_number')
        .values('end_total')[:1]
    )
    registrations = (
        Registration.objects.filter(competition_id=competition_id, category_id=category_id)
        .select_related('archer')
        .annotate(
            total_score=Coalesce(Sum(_points('score__score')), Value(0)),
            tens_count=_count(score__score__in=['10', 'X']),
            xs_count=_count(score__score='X'),
            last_end_total=Coalesce(last_end_total, Value(0)),
        )
        .order_by('-total_score', '-tens_count', '-xs_count', '-last_end_total', 'archer__name')
    )
    return [
        {
            'archer_id': r.archer_id,
            'name': r.archer.name,
            'club': r.archer.club_name,
            'score': r.total_score,
            'tens': r.tens_count,
            'xs': r.xs_count,
            'last_end_total': r.last_end_total,
        }
        for r in registrations
    ]


def competition_standings(competition):
    """Rankings for every category with registrations, categories sorted by name."""
    category_ids = Registration.objects.filter(competition=competition).values('category')
    return [
        {
            'category_id': category.id,
            'category': category.name,
            'code': category.code,
            'archers': category_ranking(competition.id, category.id),
        }
        for category in Category.objects.filter(id__in=category_ids).order_by('name')
    ]
