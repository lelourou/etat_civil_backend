from rest_framework.permissions import BasePermission


class PeutGererActeDeCentre(BasePermission):
    message = "Vous ne pouvez gérer que les actes de votre propre centre."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role in ['SUPERVISEUR_NATIONAL', 'ADMIN_SYSTEME']:
            return True
        if user.role == 'SUPERVISEUR_CENTRE':
            return obj.centre == user.centre
        if user.role == 'AGENT_GUICHET':
            return obj.centre == user.centre and obj.statut == 'BROUILLON'
        return False
