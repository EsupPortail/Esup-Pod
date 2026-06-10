"""
Esup-Pod - Dressing default configuration.
"""

USE_DRESSING = True

# Permet aux utilisateurs standards de créer leurs propres habillages.
# Si False, seuls les administrateurs peuvent les créer, les utilisateurs ne feront que choisir parmi ceux autorisés.
ALLOW_USER_CUSTOM_DRESSING = True

# Taille maximale (en Mo) autorisée pour l'upload d'images de filigrane
MAX_WATERMARK_SIZE_MB = 5

# Durée maximale (en secondes) autorisée pour les vidéos de générique (début/fin).
# Empêche d'utiliser une vidéo complète en guise de générique pour contourner des limites.
MAX_CREDITS_DURATION_SECONDS = 60

# Valeurs par défaut pour l'interface
DEFAULT_WATERMARK_OPACITY = 100
DEFAULT_WATERMARK_POSITION = "top_right"
