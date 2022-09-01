from django.conf import settings
from hashlib import sha1

BBB_API_URL = getattr(settings, "BBB_API_URL", "")
BBB_SECRET_KEY = getattr(settings, "BBB_SECRET_KEY", "")


def api_call(query, call):
    checksum_val = sha1(str(call + query + BBB_SECRET_KEY).encode("utf-8")).hexdigest()
    result = "%s&checksum=%s" % (query, checksum_val)
    return result


def parseXmlToJson(xml, sub=False):
    response = {}
    counter = 1
    for child in list(xml):
        index = child.tag
        if response.get(child.tag):
            temp_child = response[child.tag]
            response[child.tag + "__%s" % counter] = temp_child
            del response[child.tag]
        if response.get(child.tag + "__%s" % counter):
            counter += 1
            index = child.tag + "__%s" % counter

        if len(list(child)) > 0:
            response[index] = parseXmlToJson(child, sub=True)
        else:
            response[index] = child.text or ""
    return response


def slash_join(*args):
    return "/".join(arg.strip("/") for arg in args)
