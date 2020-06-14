from django.urls import path, include
from .views import DataViewSet
# data_list, data_detail, DataAPIView, DataDetails, GenericAPIView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', DataViewSet, basename='api')

urlpatterns = [
	#api con funciones
	#path('api/', data_list),
	#path('detail/<int:pk>/', data_detail),
	#api con clases
	# path('api/', DataAPIView.as_view()),
	# path('detail/<int:id>/', DataDetails.as_view()),
	#api generica
	# path('api/', GenericAPIView.as_view()),
	# path('api/<int:id>/', GenericAPIView.as_view()),
	#api DataViewSet
	# path('api/', DataViewSet.as_view()),
	# path('api/<int:id>/', DataViewSet.as_view()),
	#api con DataView mas sencillo
	path('api/', include(router.urls)),
]