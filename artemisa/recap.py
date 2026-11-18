"""AI match recap: build the standings Claude is given, and call Claude.

Used by the recap views and by `manage.py seed_demo`. A generated recap is saved on the
competition together with the exact input it was written from (`ai_recap_input`); while
the standings produce the same input, the saved text is reused and the API isn't called.
"""
import anthropic
from django.db.models import Case, F, IntegerField, Sum, Value, When
from django.db.models.functions import Cast, Coalesce

from .models import Category, Registration

RECAP_MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = (
    "You are a sports commentator writing a short, energetic recap of an archery "
    "tournament for spectators. Highlight the category leaders, standout scores "
    "(many 10s/Xs), and close finishes. Keep it to 2-3 short paragraphs of plain text "
    "(no Markdown, headings or bold), since it is shown as-is on the results page. "
    "Only use facts present in the standings below."
)


class RecapError(Exception):
    """Claude returned no usable recap (declined, or no text)."""


def get_competition_standings(competition):
    """Final standings per category, with the same scoring and tiebreakers as the
    results screen (X = 10 points and counts as an X, M = 0)."""
    registered_category_ids = Registration.objects.filter(competition=competition).values('category').distinct()
    categories = Category.objects.filter(id__in=registered_category_ids).order_by('name')

    score_value_case = Case(
        When(score__score='X', then=Value(10)),
        When(score__score='M', then=Value(0)),
        default=Cast(F('score__score'), IntegerField()),
        output_field=IntegerField(),
    )

    standings = []
    for category in categories:
        registrations = (
            Registration.objects.filter(competition=competition, category=category)
            .select_related('archer')
            .annotate(
                total_score=Coalesce(Sum(score_value_case), Value(0)),
                tens_count=Coalesce(
                    Sum(Case(When(score__score__in=['10', 'X'], then=Value(1)), default=Value(0), output_field=IntegerField())),
                    Value(0),
                ),
                xs_count=Coalesce(
                    Sum(Case(When(score__score='X', then=Value(1)), default=Value(0), output_field=IntegerField())),
                    Value(0),
                ),
            )
            .order_by('-total_score', '-tens_count', '-xs_count', 'archer__name')
        )
        standings.append({
            'category': category.name,
            'archers': [
                {'name': r.archer.name, 'score': r.total_score, 'tens': r.tens_count, 'xs': r.xs_count}
                for r in registrations
            ],
        })
    return standings


def recap_input(competition):
    """The exact text Claude receives for this competition, or None if nobody is
    registered yet. Saved next to the recap, so any change to names or scores
    makes the saved recap stale."""
    standings = get_competition_standings(competition)
    if not any(category['archers'] for category in standings):
        return None
    standings_text = "\n".join(
        f"{category['category']}: " + ", ".join(
            f"{archer['name']} ({archer['score']} pts, {archer['tens']} tens, {archer['xs']} Xs)"
            for archer in category['archers']
        )
        for category in standings
    )
    return f"Competition: {competition.name}\n\nFinal standings by category:\n{standings_text}"


def saved_recap(competition, current_input):
    """The saved recap if it was written from `current_input`, otherwise ""."""
    if competition.ai_recap and current_input and competition.ai_recap_input == current_input:
        return competition.ai_recap
    return ""


def generate_recap(prompt_input):
    """Ask Claude for a recap of `prompt_input`. Raises on API errors and RecapError
    when the reply has no usable text."""
    client = anthropic.Anthropic()
    response = client.beta.messages.create(
        model=RECAP_MODEL,
        max_tokens=16000,
        output_config={"effort": "medium"},
        # If the model declines, the API retries on a fallback model in the same call.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt_input}],
    )
    if response.stop_reason == "refusal":
        raise RecapError("The model declined to write this recap.")
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if not text:
        raise RecapError("The model returned no recap text.")
    return text
