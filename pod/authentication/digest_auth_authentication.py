# took from https://github.com/Multiposting/django-rest-framework-digestauth/tree/master/rest_framework_digestauth

import os
import hashlib
from importlib import import_module

from django.core.signing import Signer
from django.contrib.auth import get_user_model
from django.conf import settings

from rest_framework import exceptions
from rest_framework import authentication

from .utils import parse_dict_header

from .digest_backend import DatabaseBackend

User = get_user_model()
"""
backend_path = getattr(
    settings,
    'DIGESTAUTH_BACKEND',
    'rest_framework_digestauth.backends.DatabaseBackend',
).split('.')
DigestBackend = getattr(import_module('.'.join(backend_path[:-1])), backend_path[-1])
"""

class DigestAuthentication(authentication.BaseAuthentication):
    """
    HTTP Digest authentication against username/password.
    Compliant with RFC 2617 (http://tools.ietf.org/html/rfc2617).
    """
    realm = 'django-rest-framework'
    hash_algorithms = {
        'MD5': hashlib.md5,
        'MD5-sess': hashlib.md5,
        'SHA': hashlib.sha1}
    algorithm = 'MD5'  # 'MD5'/'SHA'/'MD5-sess'
    # quality of protection
    qop = 'auth'  # 'auth'/'auth-int'/None
    opaque = Signer().sign('DRFOPAQUE')

    def authenticate(self, request):
        if 'HTTP_AUTHORIZATION' in request.META:
            try:
                self.parse_authorization_header(request.META['HTTP_AUTHORIZATION'])
            except exceptions.ParseError:
                return None
            self.check_authorization_request_header()
            user = self.get_user()
            print(user)
            self.backend = DatabaseBackend(user)
            password = self.backend.get_password()
            print(password)
            if self.check_digest_auth(request, password):
                return user, None

    def authenticate_header(self, request):
        """
        Builds the WWW-Authenticate response header
        """
        nonce_data = '%s:%s' % (self.realm, os.urandom(8))
        nonce = self.hash_func(nonce_data)

        header_format = 'Digest realm="%(realm)s", qop="%(qop)s",' \
                        ' nonce="%(nonce)s", opaque="%(opaque)s",' \
                        ' algorithm="%(algorithm)s"'
        header_values = {
            'realm': self.realm,
            'qop': self.qop,
            'algorithm': self.algorithm,
            'opaque': self.opaque,
            'nonce': nonce}
        header = header_format % header_values
        return header

    def parse_authorization_header(self, auth_header):
        if not auth_header.startswith('Digest '):
            raise exceptions.ParseError('Header do not start with Digest')
        auth_header = auth_header.replace('Digest ', '')
        self.auth_header = parse_dict_header(auth_header)

    def check_authorization_request_header(self):
        """
        The values of the opaque and algorithm fields must be those supplied
        in the WWW-Authenticate response header
        """
        required_fields = ('username', 'realm', 'nonce', 'uri',
                           'response', 'algorithm', 'opaque')

        for field in required_fields:
            if field not in self.auth_header:
                raise exceptions.ParseError(
                    'Required field %s not found' % field)

        for field in ('opaque', 'algorithm', 'realm', 'qop'):
            if not self.auth_header[field] == getattr(self, field):
                raise exceptions.ParseError('%s provided not valid' % field)

        qop = self.auth_header.get('qop')
        if qop in ('auth', 'auth-int'):
            for c in ('nc', 'cnonce'):
                if c not in self.auth_header:
                    raise exceptions.ParseError('%s is required' % c)
        if not qop:
            for c in ('nc', 'cnonce'):
                if c in self.auth_header:
                    raise exceptions.ParseError('%s provided without qop' % c)

    def get_user(self):
        username = self.auth_header['username']
        try:
            username_field = 'username'
            if hasattr(User, 'USERNAME_FIELD'):
                username_field = User.USERNAME_FIELD
            args = {username_field: username}
            user = User.objects.get(**args)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            raise exceptions.PermissionDenied
        return user

    def check_digest_auth(self, request, password):
        """
        Check user authentication using HTTP Digest auth
        """
        print(self.auth_header)
        
        last_counter = self.backend.get_counter(
            self.auth_header['nonce'],
            self.auth_header['cnonce'],
        )
        current_counter = int(self.auth_header['nc'], 16)
        print(current_counter)
        """
        if last_counter is not None and not last_counter < current_counter:
            raise exceptions.AuthenticationFailed
        else:
            self.backend.set_counter(
                self.auth_header['nonce'],
                self.auth_header['cnonce'],
                current_counter
            )
        """
        response_hash = self.generate_response(request, password)
        return response_hash == self.auth_header['response']

    def generate_response(self, request, password):
        """
        Compile digest auth response

        If the qop directive's value is "auth" or "auth-int":
           RESPONSE = HASH(HA1:nonce:nc:cnonce:qop:HA2)
        If the "qop" directive is not present:
        (this construction is for compatibility with RFC 2069)
           RESPONSE = MD5(HA1:nonce:HA2)
        """
        HA1_value = self.create_HA1(password)
        HA2_value = self.create_HA2(request)

        if self.auth_header.get('qop') is None:
            response_data = ':'.join((
                HA1_value,
                self.auth_header['nonce'],
                HA2_value))
            response = self.hash_func(response_data)
        else:
            # qop is 'auth' or 'auth-int'
            response_data = ":".join((HA1_value,
                                      self.auth_header['nonce'],
                                      self.auth_header['nc'],
                                      self.auth_header['cnonce'],
                                      self.auth_header['qop'],
                                      HA2_value))
            response = self.hash_func(response_data)
        return response

    def create_HA1(self, password):
        """
        Create HA1 hash

        HA1 = HASH(A1) = HASH(username:realm:password)
        """
        if self.algorithm == 'MD5-sess':
            data = ':'.join((
                self.auth_header['username'],
                self.realm,
                password))
            data_hash = self.hash_func(data)
            A1 = ':'.join((
                data_hash,
                self.auth_header['nonce'],
                self.auth_header['cnonce']))
        else:
            A1 = ':'.join((
                self.auth_header['username'],
                self.realm,
                password))
        return self.hash_func(A1)

    def create_HA2(self, request):
        """
        Create HA2 hash

        If the "qop" directive's value is "auth" or is unspecified,
         then HA2 is:
            HA2 = HASH(A2) = HASH(request-method:digest-URI)
        If the qop directive's value is "auth-int", then HA2 is
            HA2 = HASH(A2) = HASH(request-method:digest-URI:MD5(entityBody))
        """

        if self.auth_header.get('qop') in ('auth', None):
            A2 = ':'.join((request.method, self.auth_header['uri']))
            return self.hash_func(A2)
        elif self.auth_header.get('qop') == 'auth-int':
            body_hash = self.hash_func(request.body)
            A2 = ':'.join((request.method,
                           self.auth_header['uri'],
                           body_hash))
            return self.hash_func(A2)

    def hash_func(self, data):
        alg_hash_func = self.hash_algorithms[self.algorithm]
        return alg_hash_func(data.encode()).hexdigest()
