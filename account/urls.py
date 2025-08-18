from django.urls import path
from .views import StaffLoginAPIView

urlpatterns = [
	path('staff-login/', StaffLoginAPIView.as_view(), name='staff-login'),
]