from django.urls import path

from .views import staff_login

urlpatterns = [
	path('staff-login/', staff_login, name='staff-login'),
]