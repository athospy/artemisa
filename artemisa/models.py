from django.db import models

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


class Score(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE)
    score = models.CharField(max_length=10)
    end_number = models.IntegerField(default=0)
    shoot_number = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.registration.archer.name} | {self.end_number} | {self.shoot_number} | {self.score}'
