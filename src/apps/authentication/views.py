from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema
from .serializers.CustomTokenObtainPairSerializer import CustomTokenObtainPairSerializer
from .serializers.UserSerializer import UserSerializer

class LoginView(TokenObtainPairView):
    """
    **Authentication Endpoint**
    
    Accepts a username and password and returns a pair of JWT tokens (Access & Refresh).
    This endpoint checks credentials against the local database.
    
    - **access**: Used to authenticate subsequent requests (Bearer token).
    - **refresh**: Used to obtain a new access token when the current one expires.
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserMeView(APIView):
    """
    **Current User Profile**
    
    Returns the profile information of the currently authenticated user.
    Useful for verifying the validity of a token and retrieving user context (affiliation, rights).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        serializer = UserSerializer(request.user)
        data = serializer.data
        if hasattr(request.user, 'owner'):
            data['affiliation'] = request.user.owner.affiliation
            data['establishment'] = request.user.owner.establishment
            
        return Response(data, status=status.HTTP_200_OK)