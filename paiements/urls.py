from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DemandeCopieViewSet

router = DefaultRouter()
router.register('', DemandeCopieViewSet, basename='demande-copie')

urlpatterns = [path('', include(router.urls))]
