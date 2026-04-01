"""
Esup-Pod - Legacy views for V4 compatibility.
"""

from django.http import HttpResponsePermanentRedirect


def redirect_v4_download(request, res, slug_with_ext):
    """
    Redirige les anciens liens de téléchargement vers l'API de streaming V5.
    Capture /video/telecharger/<res>/<slug>.mp4
    """
    # On retire l'extension pour obtenir le slug
    slug = slug_with_ext.rsplit(".", 1)[0]

    # Construction de l'URL vers le nouvel endpoint API
    # Le paramètre resolution est passé en query string
    new_url = f"/api/videos/{slug}/stream/?resolution={res}"

    # Utilisation d'une redirection 301 pour la pérennité des liens indexés
    return HttpResponsePermanentRedirect(new_url)
