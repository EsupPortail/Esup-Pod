# took from https://github.com/Multiposting/django-rest-framework-digestauth/tree/master/rest_framework_digestauth
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
# from rest_framework_digestauth.models import DigestAuthCounter


class AbstractDigestBackend(object):

    def __init__(self, user):
        self.user = user # This user is *unauthenticated*, beware.

    def get_password(self):
        """
        This should return a plain text password, or something that can be used
        in it's place, such as a token. Exactly what is used and how it's
        generated much be pre-negotiated with all clients.
        """
        raise NotImplementedError

    def get_counter(self, server_nonce, client_nonce):
        """
        This should return an integer, which should be equal to the last call
        to `set_counter` or None was not previously a counter set.
        """
        raise NotImplementedError

    def set_counter(self, server_nonce, client_nonce, counter):
        """
        This method should store the counter, to be returned at a later date
        when `get_counter` is called.
        """
        raise NotImplementedError


class DatabaseBackend(AbstractDigestBackend):

    def get_password(self):
        try:
            token = Token.objects.get(user=self.user)
        except (Token.DoesNotExist,
                Token.MultipleObjectsReturned):
            raise exceptions.AuthenticationFailed
        return token.key

    def get_counter(self, server_nonce, client_nonce):
        print(server_nonce, client_nonce)
        return 1
        """
        try:
            auth_counter = DigestAuthCounter.objects.get(
                server_nonce=server_nonce,
                client_nonce=client_nonce,
            )
        except DigestAuthCounter.DoesNotExist:
            return None

        return auth_counter.client_counter
        """

    def set_counter(self, server_nonce, client_nonce, counter):
        print(server_nonce, client_nonce, counter)
        """
        auth_counter, __ = DigestAuthCounter.objects.get_or_create(
            server_nonce=server_nonce,
            client_nonce=client_nonce,
        )
        auth_counter.client_counter = counter
        auth_counter.save()
        """
