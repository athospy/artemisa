from django.contrib import admin

from .models import Competition
from .models import Category
from .models import Archer
from .models import Registration
from .models import Score


admin.site.register(Competition)
admin.site.register(Archer)
admin.site.register(Category)
admin.site.register(Registration)
admin.site.register(Score)
