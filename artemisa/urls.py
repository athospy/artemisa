from django.urls import path

from . import views

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
