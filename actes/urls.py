from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActeViewSet

router = DefaultRouter()
router.register('', ActeViewSet, basename='acte')

urlpatterns = [path('', include(router.urls))]
