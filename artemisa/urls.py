from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("demo/", views.demo, name="demo"),
    path("competitions", views.competitions, name="competitions"),
    path("add_competition/", views.add_competition, name="add_competition"),
    path("add_category/", views.add_category, name="add_category"),
    path("add_archer/", views.add_archer, name="add_archer"),
    path("add_registration/", views.add_registration, name="add_registration"),
    path("select_competition/<int:competition_id>", views.select_competition, name="select_competition"),
    path("compete/<int:competition_id>", views.compete, name="compete"),
    path("add_score_div", views.add_score_div, name="add_score_div"),
    path("add_archer_div", views.add_archer_div, name="add_archer_div"),
    path("save_score_db", views.save_score_db, name="save_score_db"),
    path("result_screen/<int:competition_id>", views.result_screen, name="result_screen"),
    path("result_category", views.result_category, name="result_category"),
    path("shoot_timer/<int:competition_id>", views.shoot_timer, name="shoot_timer"),
    path("get_archer_scores", views.get_archer_scores, name="get_archer_scores"),
    path("match_recap/<int:competition_id>", views.match_recap, name="match_recap"),
    path("generate_match_recap/<int:competition_id>", views.generate_match_recap, name="generate_match_recap"),
]
