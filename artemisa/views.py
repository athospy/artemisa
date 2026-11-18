from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
import json
from collections import defaultdict
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import IntegrityError
from django.http import JsonResponse, Http404
from django.contrib.auth.views import redirect_to_login
import logging

from .models import Competition
from .models import Registration
from .models import Category
from .models import Archer
from .models import Score
from . import recap, standings
from .forms import CompetitionForm, CategoryForm, ArcherForm, RegistrationForm

logger = logging.getLogger(__name__)

@ensure_csrf_cookie
def index(request):
    from .models import Competition, Archer, Registration, Score
    stats = {
        'competitions_count': Competition.objects.count(),
        'archers_count': Archer.objects.count(),
        'registrations_count': Registration.objects.count(),
        'scores_count': Score.objects.count(),
        'has_demo': Competition.objects.filter(is_demo=True).exists(),
    }
    return render(request, "home.html", stats)


def _can_view(request, competition):
    """Logged-in users see every competition; visitors only see the demo one."""
    return request.user.is_authenticated or competition.is_demo


@ensure_csrf_cookie
def demo(request):
    """Public landing page for the demo tournament (read-only: results and timer).
    Unlike select_competition it does not touch the session, so it never changes
    which competition a logged-in scorer is saving scores into."""
    competition = Competition.objects.filter(is_demo=True).order_by('-event_date').first()
    if competition is None:
        raise Http404("No demo competition. Run: python manage.py seed_demo")
    return render(request, "competition.html", {
        'competition': competition,
        'read_only': True,
    })


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

@ensure_csrf_cookie
def result_screen(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    if not _can_view(request, competition):
        return redirect_to_login(request.get_full_path())
    registrations_categories = Registration.objects.filter(competition=competition).values('category').distinct()
    categories = Category.objects.filter(id__in=registrations_categories)

    return render(request, "result_screen.html",{
        'competition': competition,
        'categories': categories,
    })

def result_category(request):
    data = json.loads(request.body)
    # The results page sends its own competition_id. The session fallback keeps
    # older pages working; it used to be the only source, which showed the wrong
    # leaderboard when the session pointed at a different competition.
    competition_id = data.get('competition_id')
    if competition_id is None and request.session.get('current_competition'):
        competition_id = json.loads(request.session['current_competition'])['id']
    if not str(competition_id).isdigit():
        return JsonResponse({"error": "A numeric competition_id is required"}, status=400)
    competition = get_object_or_404(Competition, pk=int(competition_id))
    if not _can_view(request, competition):
        return JsonResponse({"error": "Login required"}, status=403)
    ranking = standings.category_ranking(competition.id, data['category_id'])
    # Same fields the results screen has always received.
    archer_list = [
        {key: archer[key] for key in ('name', 'score', 'tens', 'xs', 'last_end_total')}
        for archer in ranking
    ]
    return JsonResponse({"data": json.dumps(archer_list)}, status=200)


@ensure_csrf_cookie
def shoot_timer(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    if not _can_view(request, competition):
        return redirect_to_login(request.get_full_path())

    return render(request, "shoot_timer.html",{
        'competition': competition,
    })


@ensure_csrf_cookie
def match_recap(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    if not _can_view(request, competition):
        return redirect_to_login(request.get_full_path())
    current_input = recap.recap_input(competition)
    return render(request, "match_recap.html", {
        "competition": competition,
        "saved_recap": recap.saved_recap(competition, current_input),
        "has_scores": current_input is not None,
    })


def generate_match_recap(request, competition_id):
    """Return the competition's AI recap. A saved recap is reused while the standings
    are unchanged, so Claude is only called when there is something new to write
    about, and only for logged-in users (visitors never trigger an API call)."""
    competition = get_object_or_404(Competition, pk=competition_id)
    if not _can_view(request, competition):
        return JsonResponse({"error": "Login required"}, status=403)

    current_input = recap.recap_input(competition)
    if current_input is None:
        return JsonResponse({"error": "No scores recorded yet for this competition."}, status=400)

    saved = recap.saved_recap(competition, current_input)
    if saved:
        return JsonResponse({"recap": saved})
    if not request.user.is_authenticated:
        return JsonResponse({"error": "No AI recap has been written for these results yet."}, status=404)

    try:
        recap_text = recap.generate_recap(current_input)
    except Exception:
        # Runs live during a tournament: never let an API problem break the page.
        logger.exception("AI match recap failed for competition %s", competition.id)
        return JsonResponse({"error": "Could not generate the recap right now. Please try again."}, status=502)

    competition.ai_recap = recap_text
    competition.ai_recap_input = current_input
    competition.save(update_fields=["ai_recap", "ai_recap_input", "updated_at"])
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
