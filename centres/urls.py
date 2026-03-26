from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CentreViewSet, RattachementVillageViewSet, StatsDashboardView

# Routeur séparé pour les rattachements — doit être résolu AVANT le {pk} du CentreViewSet
rattachement_router = DefaultRouter()
rattachement_router.register('', RattachementVillageViewSet, basename='rattachement')

centre_router = DefaultRouter()
centre_router.register('', CentreViewSet, basename='centre')

urlpatterns = [
    path('stats/',          StatsDashboardView.as_view(), name='stats-dashboard'),
    path('rattachements/',  include(rattachement_router.urls)),   # avant {pk}/
    path('',                include(centre_router.urls)),
]
