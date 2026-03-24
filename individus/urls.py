from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IndividuViewSet

router = DefaultRouter()
router.register('', IndividuViewSet, basename='individu')

urlpatterns = [path('', include(router.urls))]
