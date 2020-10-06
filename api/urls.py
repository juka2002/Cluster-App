from django.urls import path, include
from . import views
from .views import DataViewSet, DataAnalysisSet, UserViewSet
# data_list, data_detail, DataAPIView, DataDetails, GenericAPIView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)

router = DefaultRouter()
router.register('api', DataViewSet)
router.register('api-seg', DataAnalysisSet)
router.register('users',UserViewSet)

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
	path('', include(router.urls)),
	path('cluster/', views.cluster_function),
	path('api-token/', TokenObtainPairView.as_view()),
	path('api-token-refresh/', TokenRefreshView.as_view()),
]