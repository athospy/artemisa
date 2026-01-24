from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


ALLOWED_SCORES = {"M", "X", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1", "0"}


def validate_score(value: str):
    # Accept only archery scores: 0-10, X (counts as 10), M (miss)
    if value not in ALLOWED_SCORES:
        raise ValidationError("Invalid score. Use 0-10, X, or M.")

class Competition(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=300)
    event_date = models.DateTimeField()
    location = models.CharField(max_length=200)
    code = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} | {self.code}'

    class Meta:
        permissions = [
            ("can_score", "Can enter and edit scores"),
            ("can_view_results", "Can view competition results"),
            ("can_use_timer", "Can operate shoot timer"),
        ]

class Category(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} | {self.code}'

class Archer(models.Model):
    name = models.CharField(max_length=200)
    club_name = models.CharField(max_length=200)
    email = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} | {self.email}'


class Registration(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    archer = models.ForeignKey(Archer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.competition.name} | {self.category.name} | {self.archer.name}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["competition", "category", "archer"],
                name="unique_archer_registration",
            ),
        ]


class Score(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE)
    score = models.CharField(max_length=10, validators=[validate_score])
    end_number = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(12)])
    shoot_number = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(6)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.registration.archer.name} | {self.end_number} | {self.shoot_number} | {self.score}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["registration", "end_number", "shoot_number"],
                name="unique_score_per_arrow",
            ),
        ]
        indexes = [
            models.Index(fields=["registration", "end_number"]),
        ]
