from rest_framework.permissions import BasePermission


class EstAgentCentre(BasePermission):
    """Seul un AGENT_CENTRE authentifié peut accéder aux actes."""
    message = "Accès réservé aux agents de centre."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'AGENT_CENTRE'
        )


class PeutGererActeDeCentre(BasePermission):
    """Un agent ne peut modifier que les actes de son propre centre."""
    message = "Vous ne pouvez gérer que les actes de votre propre centre."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'AGENT_CENTRE'
        )

    def has_object_permission(self, request, view, obj):
        return obj.centre == request.user.centre
