from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
import json
from collections import defaultdict
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import IntegrityError
from django.http import JsonResponse
from django.db.models import Sum, Case, When, Value, IntegerField, OuterRef, Subquery, F
from django.db.models.functions import Coalesce, Cast
from django.contrib.auth import login
import anthropic

from .models import Competition
from .models import Registration
from .models import Category
from .models import Archer
from .models import Score
from .forms import RegisterForm, CompetitionForm, CategoryForm, ArcherForm, RegistrationForm

@ensure_csrf_cookie
def index(request):
    from .models import Competition, Archer, Registration, Score
    stats = {
        'competitions_count': Competition.objects.count(),
        'archers_count': Archer.objects.count(),
        'registrations_count': Registration.objects.count(),
        'scores_count': Score.objects.count(),
    }
    return render(request, "home.html", stats)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('competitions')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
@ensure_csrf_cookie
def competitions(request):
    competitions = Competition.objects.all()
    return render(request, "competitions.html",{
        'competitions': competitions
    })


@login_required
@ensure_csrf_cookie
def add_competition(request):
    if request.method == 'POST':
        form = CompetitionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('competitions')
    else:
        form = CompetitionForm()
    return render(request, 'add_competition.html', {'form': form})


@login_required
@ensure_csrf_cookie
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('competitions')
    else:
        form = CategoryForm()
    return render(request, 'add_category.html', {'form': form})


@login_required
@ensure_csrf_cookie
def add_archer(request):
    if request.method == 'POST':
        form = ArcherForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('competitions')
    else:
        form = ArcherForm()
    return render(request, 'add_archer.html', {'form': form})


@login_required
@ensure_csrf_cookie
def add_registration(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('competitions')
    else:
        form = RegistrationForm()
    return render(request, 'add_registration.html', {'form': form})


@login_required
@ensure_csrf_cookie
def select_competition(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    competition_data = {
        'id': competition.id,
        'name': competition.name,
    }
    request.session['current_competition'] = json.dumps(competition_data)
    return render(request, "competition.html",{
        'competition': competition
    })


@login_required
@ensure_csrf_cookie
def compete(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    categories = Category.objects.all()
    registrations = (
        Registration.objects.filter(competition=competition)
        .select_related("archer", "category")
    )

    categories_map = defaultdict(list)
    for registration in registrations:
        categories_map[registration.category_id].append(registration.archer)

    categories_with_archers = [(category, categories_map[category.id]) for category in categories]

    archers = Archer.objects.all()
    archer_map = {archer.id: archer.name for archer in archers}

    return render(request, "compete.html",{
        'competition': competition,
        'categories_with_archers': categories_with_archers,
        'categories': categories,
        'archer_map': json.dumps(archer_map)
    })

@login_required
def add_score_div(request):
    data = json.loads(request.body)
    end_number = data['end_number']
    archer_id = data['archer_id']
    return render(request, "score_div.html",{
        'end_number': end_number,
        'archer_id': archer_id,
    })

@login_required
def add_archer_div(request):
    data = json.loads(request.body)
    archer_id = data['archer_id']
    archer = get_object_or_404(Archer, pk=archer_id)
    return render(request, "archer_div.html",{
        'archer': archer,
    })


@login_required
def save_score_db(request):
    data = json.loads(request.body)
    archer_id = data['archer_id']
    end_number = data['end_number']
    shoot_array = data['shoot_array']
    category_id = data['category_id']
    competition_json = json.loads(request.session['current_competition'])
    archer = get_object_or_404(Archer, pk=archer_id)
    category = get_object_or_404(Category, pk=category_id)
    competition = get_object_or_404(Competition, pk=competition_json['id'])
    try:
        registration = Registration.objects.filter(competition=competition, category=category, archer=archer).first()
        for index, score_value in enumerate(shoot_array):
            Score.objects.update_or_create(
                registration=registration,
                end_number=end_number,
                shoot_number=index + 1,
                defaults={"score": score_value},
            )
    except IntegrityError:
        return JsonResponse({
            "error": "error saving score"
        }, status=400)

    return JsonResponse({"message": "Score saved successfully."}, status=201)

@login_required
@ensure_csrf_cookie
def result_screen(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    registrations_categories = Registration.objects.filter(competition=competition).values('category').distinct()
    categories = Category.objects.filter(id__in=registrations_categories)

    return render(request, "result_screen.html",{
        'competition': competition,
        'categories': categories,
    })

@login_required
def result_category(request):
    data = json.loads(request.body)
    competition_json = json.loads(request.session['current_competition'])
    competition_id = competition_json['id']
    category_id = data['category_id']

    # Expression for summing scores via Registration -> Score reverse relation
    score_value_case_reg = Case(
        When(score__score='X', then=Value(10)),
        When(score__score='M', then=Value(0)),
        default=Cast(F('score__score'), IntegerField()),
        output_field=IntegerField(),
    )

    # Expression for computing last end total inside a Score subquery
    score_value_case_score = Case(
        When(score='X', then=Value(10)),
        When(score='M', then=Value(0)),
        default=Cast('score', IntegerField()),
        output_field=IntegerField(),
    )

    registrations = (
        Registration.objects.filter(competition_id=competition_id, category_id=category_id)
        .select_related('archer')
        .annotate(
            total_score=Coalesce(Sum(score_value_case_reg), Value(0)),
            tens_count=Coalesce(
                Sum(
                    Case(
                        When(score__score__in=['10', 'X'], then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                ),
                Value(0),
            ),
            xs_count=Coalesce(
                Sum(
                    Case(
                        When(score__score='X', then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                ),
                Value(0),
            ),
            last_end_total=Coalesce(
                Subquery(
                    Score.objects.filter(registration=OuterRef('pk'))
                    .values('end_number')
                    .annotate(end_total=Sum(score_value_case_score))
                    .order_by('-end_number')
                    .values('end_total')[:1]
                ),
                Value(0),
            ),
        )
        .order_by('-total_score', '-tens_count', '-xs_count', '-last_end_total')
    )

    archer_list = [
        {
            'name': registration.archer.name,
            'score': registration.total_score,
            'tens': registration.tens_count,
            'xs': registration.xs_count,
            'last_end_total': registration.last_end_total,
        }
        for registration in registrations
    ]

    return JsonResponse({"data": json.dumps(archer_list)}, status=200)


@login_required
@ensure_csrf_cookie
def shoot_timer(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)

    return render(request, "shoot_timer.html",{
        'competition': competition,
    })


def _get_competition_standings(competition):
    """Final standings per category for a competition, using the same scoring
    and tiebreaker rules as result_category (X=10+tiebreaker, M=0)."""
    registered_category_ids = Registration.objects.filter(competition=competition).values('category').distinct()
    categories = Category.objects.filter(id__in=registered_category_ids)

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
            .order_by('-total_score', '-tens_count', '-xs_count')
        )
        standings.append({
            'category': category.name,
            'archers': [
                {'name': r.archer.name, 'score': r.total_score, 'tens': r.tens_count, 'xs': r.xs_count}
                for r in registrations
            ],
        })
    return standings


@login_required
@ensure_csrf_cookie
def match_recap(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    return render(request, "match_recap.html", {"competition": competition})


@login_required
def generate_match_recap(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    standings = _get_competition_standings(competition)

    if not any(category['archers'] for category in standings):
        return JsonResponse({"error": "No scores recorded yet for this competition."}, status=400)

    standings_text = "\n".join(
        f"{category['category']}: " + ", ".join(
            f"{archer['name']} ({archer['score']} pts, {archer['tens']} tens, {archer['xs']} Xs)"
            for archer in category['archers']
        )
        for category in standings
    )

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            system=(
                "You are a sports commentator writing a short, energetic recap of an archery "
                "tournament for spectators. Highlight the category leaders, standout scores "
                "(many 10s/Xs), and close finishes. Keep it to 2-3 short paragraphs. Only use "
                "facts present in the standings below."
            ),
            messages=[{
                "role": "user",
                "content": f"Competition: {competition.name}\n\nFinal standings by category:\n{standings_text}",
            }],
        )
    except Exception:
        return JsonResponse({"error": "Could not generate the recap right now. Please try again."}, status=502)

    recap_text = next((block.text for block in response.content if block.type == "text"), "")
    return JsonResponse({"recap": recap_text})


@login_required
def get_archer_scores(request):
    data = json.loads(request.body)
    archer_id = int(data.get('archer_id'))
    category_id = int(data.get('category_id'))
    competition_json = json.loads(request.session['current_competition'])
    competition_id = competition_json['id']

    registration = (
        Registration.objects
        .filter(competition_id=competition_id, category_id=category_id, archer_id=archer_id)
        .first()
    )

    if not registration:
        return JsonResponse({"scores": []}, status=200)

    scores = (
        Score.objects
        .filter(registration=registration)
        .values('end_number', 'shoot_number', 'score')
        .order_by('end_number', 'shoot_number')
    )

    return JsonResponse({"scores": list(scores)}, status=200)
