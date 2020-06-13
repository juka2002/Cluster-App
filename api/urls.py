from django.urls import path
from MiApp.views import data_list

urlpatterns = [
	path('api/', data_list),
]