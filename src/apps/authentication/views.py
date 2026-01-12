import logging
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import filters, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
try:
    from django_cas_ng.utils import get_cas_client
except ImportError:
    get_cas_client = None
from .models.AccessGroup import AccessGroup
from .models.Owner import Owner
from .models.utils import AFFILIATION_STAFF, DEFAULT_AFFILIATION
from .serializers.AccessGroupSerializer import AccessGroupSerializer
from .serializers.CASTokenObtainPairSerializer import (
    CASTokenObtainPairSerializer
)
from .serializers.CustomTokenObtainPairSerializer import (
    CustomTokenObtainPairSerializer
)
from .serializers.ExternalAuthSerializers import (
    OIDCTokenObtainSerializer,
    ShibbolethTokenObtainSerializer
)
from .serializers.GroupSerializer import GroupSerializer
from .serializers.OwnerSerializer import (
    OwnerSerializer,
    OwnerWithGroupsSerializer
)
from .serializers.SiteSerializer import SiteSerializer
from .serializers.UserSerializer import UserSerializer

User = get_user_model()
logger = logging.getLogger(__name__)

CREATE_GROUP_FROM_AFFILIATION = getattr(
    settings, "CREATE_GROUP_FROM_AFFILIATION", False
)

REMOTE_USER_HEADER = getattr(settings, "REMOTE_USER_HEADER", "REMOTE_USER")
SHIBBOLETH_ATTRIBUTE_MAP = getattr(
    settings,
    "SHIBBOLETH_ATTRIBUTE_MAP",
    {
        "REMOTE_USER": (True, "username"),
        "Shibboleth-givenName": (True, "first_name"),
        "Shibboleth-sn": (False, "last_name"),
        "Shibboleth-mail": (False, "email"),
        "Shibboleth-primary-affiliation": (False, "affiliation"),
        "Shibboleth-unscoped-affiliation": (False, "affiliations"),
    },
)
SHIBBOLETH_STAFF_ALLOWED_DOMAINS = getattr(
    settings, "SHIBBOLETH_STAFF_ALLOWED_DOMAINS", None
)

OIDC_CLAIM_GIVEN_NAME = getattr(
    settings, "OIDC_CLAIM_GIVEN_NAME", "given_name"
)
OIDC_CLAIM_FAMILY_NAME = getattr(
    settings, "OIDC_CLAIM_FAMILY_NAME", "family_name"
)
OIDC_CLAIM_PREFERRED_USERNAME = getattr(
    settings, "OIDC_CLAIM_PREFERRED_USERNAME", "preferred_username"
)
OIDC_DEFAULT_AFFILIATION = getattr(
    settings, "OIDC_DEFAULT_AFFILIATION", DEFAULT_AFFILIATION
)
OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES = getattr(
    settings, "OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES", []
)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['username'] = user.username
    refresh['is_staff'] = user.is_staff
    if hasattr(user, 'owner'):
        refresh['affiliation'] = user.owner.affiliation

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'affiliation': (
                user.owner.affiliation if hasattr(user, 'owner') else None
            )
        }
    }


def is_staff_affiliation(affiliation) -> bool:
    """Check if user affiliation correspond to AFFILIATION_STAFF."""
    return affiliation in AFFILIATION_STAFF


class LoginView(TokenObtainPairView):
    """
    **Authentication Endpoint**
    Accepts a username and password and returns a pair of JWT tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserMeView(APIView):
    """
    **Current User Profile**
    Returns the profile information of the currently authenticated user.
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
    

class CASLoginView(APIView):
    """
    **CAS Authentication Endpoint**
    Exchange a valid CAS ticket for a JWT token pair.
    """
    permission_classes = [AllowAny]
    serializer_class = CASTokenObtainPairSerializer

    @extend_schema(
        request=CASTokenObtainPairSerializer,
        responses=CASTokenObtainPairSerializer
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            return Response(
                serializer.validated_data, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShibbolethLoginView(APIView):
    """
    **Shibboleth Authentication Endpoint**
        
    This view must be protected by the Shibboleth SP (Apache/Nginx)
    which injects the headers.
    It reads the headers (REMOTE_USER, etc.), creates or updates the user
    locally according to the logic defined in the former
    ShibbolethRemoteUserBackend and returns JWTs.
    and returns JWTs.
    """
    permission_classes = [AllowAny]
    serializer_class = ShibbolethTokenObtainSerializer

    def _get_header_value(self, request, header_name):
        return request.META.get(header_name, '')

    def _is_staffable(self, user) -> bool:
        """Check that given user domain is in authorized domains."""
        if not SHIBBOLETH_STAFF_ALLOWED_DOMAINS:
            return True
        for d in SHIBBOLETH_STAFF_ALLOWED_DOMAINS:
            if user.username.endswith("@" + d):
                return True
        return False

    @extend_schema(request=ShibbolethTokenObtainSerializer)
    def get(self, request, *args, **kwargs):
        username = self._get_header_value(request, REMOTE_USER_HEADER)
        if not username:
            return Response(
                {
                    "error": f"Missing {REMOTE_USER_HEADER} header. "
                             f"Shibboleth misconfigured?"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        user, created = User.objects.get_or_create(username=username)

        
        shib_meta = {}
        for header, (required, field) in SHIBBOLETH_ATTRIBUTE_MAP.items():
            value = self._get_header_value(request, header)
            if value:
                shib_meta[field] = value
                if field in ['first_name', 'last_name', 'email']:
                    setattr(user, field, value)

        user.save()
        if not hasattr(user, 'owner'):
            Owner.objects.create(user=user)

        owner = user.owner
        owner.auth_type = "Shibboleth"

        current_site = get_current_site(request)
        if current_site not in owner.sites.all():
            owner.sites.add(current_site)

        affiliation = shib_meta.get("affiliation", "")
        if affiliation:
            owner.affiliation = affiliation

            if is_staff_affiliation(affiliation):
                user.is_staff = True

            if CREATE_GROUP_FROM_AFFILIATION:
                group, _ = Group.objects.get_or_create(name=affiliation)
                user.groups.add(group)

        affiliations_str = shib_meta.get("affiliations", "")
        if self._is_staffable(user) and affiliations_str:
            for aff in affiliations_str.split(";"):
                if is_staff_affiliation(aff):
                    user.is_staff = True
                    break

        user.save()
        owner.save()

        tokens = get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_200_OK)


class OIDCLoginView(APIView):
    """
    **OIDC Authentication Endpoint**

    Exchanges an 'authorization_code' for OIDC tokens via the Provider,
    retrieves user information (UserInfo),
    updates the local database (using OIDCBackend logic), and returns JWTs.
    """
    permission_classes = [AllowAny]
    serializer_class = OIDCTokenObtainSerializer

    @extend_schema(request=OIDCTokenObtainSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        code = serializer.validated_data['code']
        redirect_uri = serializer.validated_data['redirect_uri']

        token_url = getattr(settings, "OIDC_OP_TOKEN_ENDPOINT", "")
        client_id = getattr(settings, "OIDC_RP_CLIENT_ID", "")
        client_secret = getattr(settings, "OIDC_RP_CLIENT_SECRET", "")
        
        if not token_url:
            return Response(
                {
                    "error": "OIDC not configured "
                             "(missing OIDC_OP_TOKEN_ENDPOINT)"
                },
                status=500
            )

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        
        try:
            r_token = requests.post(token_url, data=payload)
            r_token.raise_for_status()
            tokens_oidc = r_token.json()
            access_token = tokens_oidc.get("access_token")
        except Exception as e:
            logger.error(f"OIDC Token Exchange failed: {e}")
            return Response(
                {"error": "Failed to exchange OIDC code"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        userinfo_url = getattr(settings, "OIDC_OP_USER_ENDPOINT", "")
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            r_user = requests.get(userinfo_url, headers=headers)
            r_user.raise_for_status()
            claims = r_user.json()
        except Exception as e:
            logger.error(f"OIDC UserInfo failed: {e}")
            return Response(
                {"error": "Failed to fetch OIDC user info"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        username = claims.get(OIDC_CLAIM_PREFERRED_USERNAME)
        if not username:
            return Response(
                {"error": "Missing username in OIDC claims"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user, created = User.objects.get_or_create(username=username)

        user.first_name = claims.get(OIDC_CLAIM_GIVEN_NAME, user.first_name)
        user.last_name = claims.get(OIDC_CLAIM_FAMILY_NAME, user.last_name)
        user.email = claims.get("email", user.email)
        
        if not hasattr(user, 'owner'):
            Owner.objects.create(user=user)
        
        user.owner.auth_type = "OIDC"
        
        if created or not user.owner.affiliation:
            user.owner.affiliation = OIDC_DEFAULT_AFFILIATION

        for code_name in OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES:
            try:
                group = AccessGroup.objects.get(code_name=code_name)
                user.owner.accessgroups.add(group)
            except AccessGroup.DoesNotExist:
                pass
        
        user.is_staff = is_staff_affiliation(user.owner.affiliation)
        
        user.save()
        user.owner.save()

        tokens = get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_200_OK)


class OwnerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Owner profiles.
    Includes actions to manage access groups for a user.
    """
    queryset = Owner.objects.all().order_by("-user")
    serializer_class = OwnerSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='set-user-accessgroup')
    def set_user_accessgroup(self, request):
        """
        Equivalent of accessgroups_set_user_accessgroup. 
        Assigns AccessGroups to a user via their username.
        """
        username = request.data.get("username")
        groups = request.data.get("groups")
        
        if not username or groups is None:
            return Response(
                {"error": "Missing username or groups"},
                status=status.HTTP_400_BAD_REQUEST
            )

        owner = get_object_or_404(Owner, user__username=username)

        for group_code in groups:
            try:
                accessgroup = AccessGroup.objects.get(code_name=group_code)
                owner.accessgroups.add(accessgroup)
            except AccessGroup.DoesNotExist:
                pass

        serializer = OwnerWithGroupsSerializer(
            instance=owner, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='remove-user-accessgroup')
    def remove_user_accessgroup(self, request):
        """
        Equivalent of accessgroups_remove_user_accessgroup. 
        Removes AccessGroups from a user via their username.
        """
        username = request.data.get("username")
        groups = request.data.get("groups")
        
        if not username or groups is None:
            return Response(
                {"error": "Missing username or groups"},
                status=status.HTTP_400_BAD_REQUEST
            )

        owner = get_object_or_404(Owner, user__username=username)

        for group_code in groups:
            try:
                accessgroup = AccessGroup.objects.get(code_name=group_code)
                if accessgroup in owner.accessgroups.all():
                    owner.accessgroups.remove(accessgroup)
            except AccessGroup.DoesNotExist:
                pass

        serializer = OwnerWithGroupsSerializer(
            instance=owner, context={"request": request}
        )
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing standard Django Users.
    """
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    filterset_fields = ["id", "username", "email"]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]  # Ajout du backend de recherche
    search_fields = ['username', 'first_name', 'last_name', 'email']


class GroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Django Groups (Permissions).
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]


class SiteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Sites.
    """
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = [IsAuthenticated]


class AccessGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Access Groups.
    Includes actions to add/remove users by code name.
    """
    queryset = AccessGroup.objects.all()
    serializer_class = AccessGroupSerializer
    filterset_fields = ["id", "display_name", "code_name"]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='set-users-by-name')
    def set_users_by_name(self, request):
        """
        Equivalent of accessgroups_set_users_by_name.
        Adds a list of users (by username) to an AccessGroup (by code_name).
        """
        code_name = request.data.get("code_name")
        users = request.data.get("users")
        
        if not code_name or users is None:
            return Response(
                {"error": "Missing code_name or users"},
                status=status.HTTP_400_BAD_REQUEST
            )

        accessgroup = get_object_or_404(AccessGroup, code_name=code_name)
        
        for username in users:
            try:
                owner = Owner.objects.get(user__username=username)
                accessgroup.users.add(owner)
            except Owner.DoesNotExist:
                pass
        
        return Response(
            AccessGroupSerializer(
                instance=accessgroup, context={"request": request}
            ).data
        )

    @action(detail=False, methods=['post'], url_path='remove-users-by-name')
    def remove_users_by_name(self, request):
        """
        Equivalent of accessgroups_remove_users_by_name.
        Removes a list of users (by username) from an AccessGroup (by code_name).
        """
        code_name = request.data.get("code_name")
        users = request.data.get("users")
        if not code_name or users is None:
            return Response(
                {"error": "Missing code_name or users"},
                status=status.HTTP_400_BAD_REQUEST
            )

        accessgroup = get_object_or_404(AccessGroup, code_name=code_name)

        
        for username in users:
            try:
                owner = Owner.objects.get(user__username=username)
                if owner in accessgroup.users.all():
                    accessgroup.users.remove(owner)
            except Owner.DoesNotExist:
                pass

        return Response(
            AccessGroupSerializer(
                instance=accessgroup,
                context={"request": request}
            ).data
        )


class LogoutInfoView(APIView):
    """
    Returns the logout URLs for external providers.
    The frontend must call this endpoint to know where
    to redirect the user after deleting the local JWT token.
    """
    permission_classes = [AllowAny]

    @extend_schema(
            responses=inline_serializer(
                name='LogoutInfoResponse',
                fields={
                    'local': serializers.CharField(allow_null=True),
                    'cas': serializers.CharField(allow_null=True),
                    'shibboleth': serializers.CharField(allow_null=True),
                    'oidc': serializers.CharField(allow_null=True),
                }
            )
        )
    def get(self, request):
        data = {
            "local": None,
            "cas": None,
            "shibboleth": None,
            "oidc": None
        }

        if getattr(settings, 'USE_CAS', False) and get_cas_client:
            try:
                client = get_cas_client(
                    service_url=request.build_absolute_uri('/')
                )
                data["cas"] = client.get_logout_url(
                    redirect_url=request.build_absolute_uri('/')
                )
            except Exception:
                pass

        if getattr(settings, 'USE_SHIB', False):
            shib_logout = getattr(settings, 'SHIB_LOGOUT_URL', '')
            if shib_logout:
                return_url = request.build_absolute_uri('/')
                data["shibboleth"] = f"{shib_logout}?return={return_url}"

        if getattr(settings, 'USE_OIDC', False):
            oidc_logout = getattr(settings, 'OIDC_OP_LOGOUT_ENDPOINT', '')
            if oidc_logout:
                data["oidc"] = oidc_logout

        return Response(data)


class LoginConfigView(APIView):
    """
    Returns the configuration of active authentication methods.
    Allows the frontend to know which login buttons to display.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            200: inline_serializer(
                name='LoginConfigResponse',
                fields={
                    'use_local': serializers.BooleanField(),
                    'use_cas': serializers.BooleanField(),
                    'use_shibboleth': serializers.BooleanField(),
                    'use_oidc': serializers.BooleanField(),
                    'shibboleth_name': serializers.CharField(),
                    'oidc_name': serializers.CharField(),
                }
            )
        }
    )
    def get(self, request):
        return Response({
            "use_local": getattr(settings, "USE_LOCAL_AUTH", True),
            "use_cas": getattr(settings, "USE_CAS", False),
            "use_shibboleth": getattr(settings, "USE_SHIB", False),
            "use_oidc": getattr(settings, "USE_OIDC", False),
            "shibboleth_name": getattr(settings, "SHIB_NAME", "Shibboleth"),
            "oidc_name": getattr(settings, "OIDC_NAME", "OpenID Connect"),
        })
