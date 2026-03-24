from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CentreViewSet, RattachementVillageViewSet

router = DefaultRouter()
router.register('',              CentreViewSet,             basename='centre')
router.register('rattachements', RattachementVillageViewSet, basename='rattachement')

urlpatterns = [path('', include(router.urls))]
