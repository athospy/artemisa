"""Create (or reset) the public demo tournament.

    python manage.py seed_demo

Visitors can open this competition's results screen and shoot timer without logging
in (see Competition.is_demo). Everything here is made up. Running the command again
deletes the demo's registrations and scores and recreates them, so it is safe to rerun
after someone edits the demo. Real competitions are never touched.
"""
import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from artemisa.models import Archer, Category, Competition, Registration, Score

DEMO_CODE = "DEMO"
DEMO_CLUB = "Demo Archery Club"
ENDS = 6
ARROWS_PER_END = 6
RANDOM_SEED = 2026  # fixed, so every reset produces the same leaderboard

# Same names and codes as the categories used at real events, so they are reused.
CATEGORIES = [
    ("CM", "Compound Bow Men"),
    ("CW", "Compound Bow Women"),
    ("RM", "Recurve Bow Men"),
    ("RW", "Recurve Bow Women"),
]

# (name, category code, skill = average points per arrow)
ARCHERS = [
    ("Mateo Benítez", "CM", 9.3), ("Lucas Ferreira", "CM", 9.0), ("Diego Acosta", "CM", 8.7),
    ("Tomás Rivas", "CM", 8.2),
    ("Valentina Ortiz", "CW", 9.2), ("Camila Duarte", "CW", 8.9), ("Sofía Giménez", "CW", 8.5),
    ("Martina López", "CW", 7.9),
    ("Nicolás Vera", "RM", 8.6), ("Joaquín Martínez", "RM", 8.3), ("Gabriel Ramírez", "RM", 7.8),
    ("Andrés Cabrera", "RM", 7.1),
    ("Lucía Fernández", "RW", 8.4), ("Isabella Romero", "RW", 8.4), ("Paula Sanabria", "RW", 7.6),
    ("Elena Torres", "RW", 7.0),
]

# Category whose top two archers end on the same total, split by the 10s tiebreaker.
TIE_CATEGORY = "RW"


def arrow_points(arrow):
    return 10 if arrow == "X" else 0 if arrow == "M" else int(arrow)


def shoot_arrow(rng, skill):
    """One arrow for an archer whose average is `skill` points."""
    points = round(rng.gauss(skill, 1.2))
    if points >= 10:
        return "X" if rng.random() < 0.4 else "10"
    if points <= 0:
        return "M"
    return str(points)


def tied_arrows(leader_arrows):
    """Arrows with the same total as leader_arrows but one fewer 10:
    one of the leader's 10s becomes a 9, and one of its lower arrows gains a point."""
    arrows = list(leader_arrows)
    ten = next(i for i, a in enumerate(arrows) if a in ("10", "X"))
    low = next(i for i, a in enumerate(arrows) if a not in ("10", "X", "9", "M"))
    arrows[ten] = "9"
    arrows[low] = str(int(arrows[low]) + 1)
    return arrows


class Command(BaseCommand):
    help = "Create or reset the public demo tournament (made-up archers and scores)."

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(RANDOM_SEED)

        competition, _ = Competition.objects.update_or_create(
            code=DEMO_CODE,
            is_demo=True,
            defaults={
                "name": "Artemisa Demo Open",
                "description": "Demo tournament with made-up archers and scores.",
                "event_date": timezone.now(),
                "location": "Demo Range",
            },
        )
        # Reset: scores are deleted with their registrations (on_delete=CASCADE).
        Registration.objects.filter(competition=competition).delete()

        categories = {}
        for code, name in CATEGORIES:
            categories[code], _ = Category.objects.get_or_create(code=code, defaults={"name": name})

        arrows_by_category = {}
        for number, (name, code, skill) in enumerate(ARCHERS, start=1):
            archer, _ = Archer.objects.update_or_create(
                email=f"demo{number}@example.com",
                defaults={"name": name, "club_name": DEMO_CLUB},
            )
            registration = Registration.objects.create(
                competition=competition, category=categories[code], archer=archer
            )
            arrows = [shoot_arrow(rng, skill) for _ in range(ENDS * ARROWS_PER_END)]
            arrows_by_category.setdefault(code, []).append((registration, arrows))

        # The top two in TIE_CATEGORY finish level on points; the leader keeps
        # first place on 10s. Shows off the tiebreaker on the results screen.
        entries = arrows_by_category[TIE_CATEGORY]
        entries.sort(key=lambda entry: -sum(arrow_points(a) for a in entry[1]))
        entries[1] = (entries[1][0], tied_arrows(entries[0][1]))

        for entries in arrows_by_category.values():
            for registration, arrows in entries:
                Score.objects.bulk_create(
                    Score(
                        registration=registration,
                        end_number=i // ARROWS_PER_END + 1,
                        shoot_number=i % ARROWS_PER_END + 1,
                        score=arrow,
                    )
                    for i, arrow in enumerate(arrows)
                )

        self.stdout.write(self.style.SUCCESS(
            f"Demo ready: '{competition.name}' (id {competition.id}), "
            f"{len(ARCHERS)} archers, {len(ARCHERS) * ENDS * ARROWS_PER_END} arrows. "
            f"Open /demo/"
        ))
