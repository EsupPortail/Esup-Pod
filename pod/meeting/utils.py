from django.conf import settings
from hashlib import sha1

BBB_API_URL = getattr(settings, "BBB_API_URL", "")
BBB_SECRET_KEY = getattr(settings, "BBB_SECRET_KEY", "")

def api_call(query, call):
    checksum_val = sha1(str(call + query + BBB_SECRET_KEY).encode('utf-8')).hexdigest()
    result = "%s&checksum=%s" % (query, checksum_val)
    return result