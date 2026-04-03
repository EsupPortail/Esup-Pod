"""
Esup-Pod - Legacy views for V4 compatibility.
"""

from django.http import HttpResponsePermanentRedirect


def redirect_v4_download(request, res, slug_with_ext):
    """
    Redirects old download links to the V5 streaming API.
    Captures /video/telechargement/<res>/<slug>.mp4
    """
    slug = slug_with_ext.rsplit(".", 1)[0]
    new_url = f"/api/videos/{slug}/stream/?resolution={res}"
    return HttpResponsePermanentRedirect(new_url)
