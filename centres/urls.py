from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CentreViewSet, RattachementVillageViewSet, StatsDashboardView

router = DefaultRouter()
router.register('',              CentreViewSet,             basename='centre')
router.register('rattachements', RattachementVillageViewSet, basename='rattachement')

urlpatterns = [
    path('stats/', StatsDashboardView.as_view(), name='stats-dashboard'),
    path('', include(router.urls)),
]
