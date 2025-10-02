from django.contrib import admin
from .models import Restaurant, MenuItem, Feedback, Table

admin.site.register(Restaurant)
admin.site.register(MenuItem)
admin.site.register(Feedback)
admin.site.register(Table)
