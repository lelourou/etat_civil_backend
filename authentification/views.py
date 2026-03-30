from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Agent
from .serializers import AgentSerializer, AgentCreateSerializer, CustomTokenObtainSerializer, ResetPasswordSerializer


class EstAdminCentral(permissions.BasePermission):
    """Seul un ADMIN_CENTRAL peut gérer les utilisateurs."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'ADMIN_CENTRAL'
        )


class LoginView(TokenObtainPairView):
    serializer_class   = CustomTokenObtainSerializer
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    def post(self, request):
        try:
            token = RefreshToken(request.data["refresh"])
            token.blacklist()
            return Response({"detail": "Déconnexion réussie."}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "Token invalide."}, status=status.HTTP_400_BAD_REQUEST)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = AgentSerializer

    def get_object(self):
        return self.request.user


class AgentListCreateView(generics.ListCreateAPIView):
    """
    GET  — liste de tous les agents (ADMIN_CENTRAL uniquement)
    POST — créer un agent (ADMIN_CENTRAL uniquement)
    """
    queryset           = Agent.objects.select_related('centre').all()
    permission_classes = [EstAdminCentral]

    def get_serializer_class(self):
        return AgentCreateSerializer if self.request.method == 'POST' else AgentSerializer


class AgentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Consultation / modification / désactivation d'un agent (ADMIN_CENTRAL)."""
    queryset           = Agent.objects.select_related('centre').all()
    serializer_class   = AgentSerializer
    permission_classes = [EstAdminCentral]


class ResetPasswordView(APIView):
    """Réinitialisation du mot de passe d'un agent par l'ADMIN_CENTRAL."""
    permission_classes = [EstAdminCentral]

    def post(self, request, pk):
        try:
            agent = Agent.objects.get(pk=pk)
        except Agent.DoesNotExist:
            return Response({'detail': 'Agent introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        agent.set_password(serializer.validated_data['new_password'])
        agent.save(update_fields=['password'])
        return Response({'detail': 'Mot de passe réinitialisé avec succès.'})
