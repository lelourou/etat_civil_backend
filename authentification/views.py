from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Agent
from .serializers import AgentSerializer, AgentCreateSerializer, CustomTokenObtainSerializer


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainSerializer
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Déconnexion réussie."}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "Token invalide."}, status=status.HTTP_400_BAD_REQUEST)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = AgentSerializer

    def get_object(self):
        return self.request.user


class AgentListCreateView(generics.ListCreateAPIView):
    queryset = Agent.objects.select_related('centre').all()

    def get_serializer_class(self):
        return AgentCreateSerializer if self.request.method == 'POST' else AgentSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class AgentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset         = Agent.objects.select_related('centre').all()
    serializer_class = AgentSerializer
    permission_classes = [permissions.IsAdminUser]
