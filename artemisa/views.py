from django.shortcuts import render
from django.shortcuts import get_object_or_404
import json
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.http import JsonResponse

from .models import Competition
from .models import Registration
from .models import Category
from .models import Archer
from .models import Score

def index(request):
    return render(request, "home.html",{})


def competitions(request):
    competitions = Competition.objects.all()
    return render(request, "competitions.html",{
        'competitions': competitions
    })


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


def compete(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    categories = Category.objects.all()
    registrations = Registration.objects.filter(competition =  competition)

    # Create a dictionary to map category_id to a list of archers
    categories_map = defaultdict(list)
    for registration in registrations:
        categories_map[registration.category_id].append(registration.archer)

    # Create a list of tuples (category, archers)
    categories_with_archers = [(category, categories_map[category.id]) for category in categories]

    archers = Archer.objects.all()
    archer_map = {}
    for archer in archers:
        archer_map[archer.id] = archer.name

    return render(request, "compete.html",{
        'competition': competition,
        'categories_with_archers': categories_with_archers,
        'categories': categories,
        'archer_map': json.dumps(archer_map)
    })

@csrf_exempt
def add_score_div(request):
    data = json.loads(request.body)
    user = request.user
    end_number = data['end_number']
    archer_id = data['archer_id']
    return render(request, "score_div.html",{
        'end_number': end_number,
        'archer_id': archer_id,
    })

@csrf_exempt
def add_archer_div(request):
    data = json.loads(request.body)
    user = request.user
    archer_id = data['archer_id']
    archer = get_object_or_404(Archer, pk=archer_id)
    return render(request, "archer_div.html",{
        'archer': archer,
    })


@csrf_exempt
def save_score_db(request):
    data = json.loads(request.body)
    user = request.user
    archer_id = data['archer_id']
    end_number = data['end_number']
    shoot_array = data['shoot_array']
    category_id = data['category_id']
    competition_json = json.loads(request.session['current_competition'])
    # print(f"archer_id: {archer_id}, shoot_array: {shoot_array}, end_number: {end_number}, category_id: {category_id}")
    archer = get_object_or_404(Archer, pk=archer_id)
    category = get_object_or_404(Category, pk=category_id)
    competition = get_object_or_404(Competition, pk=competition_json['id'])
    try:
        registration = Registration.objects.filter(competition=competition, category=category, archer=archer).first()
        # print(f"registration: {registration}")
        for index, score in enumerate(shoot_array):
            score_exist = Score.objects.filter(registration=registration, end_number=end_number, shoot_number=index+1).first()
            if score_exist != None:
                score_exist.delete()
            score = Score(registration=registration, score=score, end_number=end_number, shoot_number=index+1)
            score.save()
    except IntegrityError:
        return JsonResponse({
            "error": "error saving score"
        }, status=400)

    return JsonResponse({"message": "Score saved successfully."}, status=201)

def result_screen(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    registrations_categories = Registration.objects.filter(competition =  competition).values('category').distinct()
    categories = Category.objects.filter(id__in = registrations_categories)

    return render(request, "result_screen.html",{
        'competition': competition,
        'categories': categories,
    })

@csrf_exempt
def result_category(request):
    data = json.loads(request.body)
    competition_json = json.loads(request.session['current_competition'])
    competition_id = competition_json['id']
    category_id = data['category_id']
    registrations_archers = Registration.objects.filter(competition_id=competition_id, category_id=category_id)
    # get the last end that has score
    archer_list = []
    for registration in registrations_archers:
        print(f"registration: {registration}")
        scores = Score.objects.filter(registration_id=registration.id)
        archer = Archer.objects.get(pk=registration.archer_id)
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
    # print(f"archer_list: {archer_list}")
    # Sorting the list by score in descending order
    sorted_archer_list = sorted(archer_list, key=lambda x: x['score'], reverse=True)
    # print(f"sorted_archer_list: {sorted_archer_list}")
    return JsonResponse({"data": json.dumps(sorted_archer_list)}, status=201)


def shoot_timer(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)

    return render(request, "shoot_timer.html",{
        'competition': competition,
    })
