from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Documentation API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Apps métier
    path('api/v1/auth/',          include('authentification.urls')),
    path('api/v1/territoire/',    include('territoire.urls')),
    path('api/v1/centres/',       include('centres.urls')),
    path('api/v1/individus/',     include('individus.urls')),
    path('api/v1/actes/',         include('actes.urls')),
    path('api/v1/paiements/',     include('paiements.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
