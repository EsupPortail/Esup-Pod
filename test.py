import sys
sys.path.insert(0, '/usr/local/django_projects/Pod_V5_Back')

from pydantic_settings import BaseSettings
import src.apps.encoding.conf as encoding_conf
import src.apps.authentication.conf as auth_conf

print("Encoding:")
for attr_name in dir(encoding_conf):
    attr = getattr(encoding_conf, attr_name)
    if isinstance(attr, BaseSettings):
        print("  Matched:", attr_name)

print("Authentication:")
for attr_name in dir(auth_conf):
    attr = getattr(auth_conf, attr_name)
    if isinstance(attr, BaseSettings):
        print("  Matched:", attr_name)
