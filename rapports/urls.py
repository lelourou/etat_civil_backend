from django.urls import path
from .views import (
    SyntheseView,
    EvolutionMensuelleView,
    ActesParNatureView,
    ActesParCentreView,
    RecettesParCentreView,
    PaiementsParCanalView,
)

urlpatterns = [
    path('synthese/',           SyntheseView.as_view(),           name='rapport-synthese'),
    path('evolution-mensuelle/', EvolutionMensuelleView.as_view(), name='rapport-evolution'),
    path('par-nature/',         ActesParNatureView.as_view(),      name='rapport-nature'),
    path('par-centre/',         ActesParCentreView.as_view(),      name='rapport-centre'),
    path('recettes/',           RecettesParCentreView.as_view(),   name='rapport-recettes'),
    path('paiements-canal/',    PaiementsParCanalView.as_view(),   name='rapport-canal'),
]
