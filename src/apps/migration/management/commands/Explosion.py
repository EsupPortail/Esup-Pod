"""Esup-Pod - Migration command to import legacy data."""

from django.core.management.base import BaseCommand

from src.apps.migration.utils.userMigrate import userMigrate
from src.apps.migration.utils.videoMigrate import videoMigrate
from src.apps.migration.utils.speakerMigrate import speakerMigrate
from src.apps.migration.utils.hyperlinkMigrate import hyperlinkMigrate
from src.apps.migration.utils.documentMigrate import documentMigrate
from src.apps.migration.utils.groupingMigrate import groupingMigrate
from src.apps.migration.utils.collectionMigrate import collectionMigrate
from src.apps.migration.utils.commentMigrate import commentMigrate


class Command(BaseCommand):
    """Migration command to run all legacy data import steps in order."""

    def add_arguments(self, parser):
        """Define CLI arguments for the migration command."""
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Nombre de vidéos à migrer (défaut: 10, 0 = toutes)",
        )

    def handle(self, *args, **kwargs):
        """Execute each migration step sequentially."""
        userMigrate(self, *args, **kwargs)
        videoMigrate(self, *args, **kwargs)
        speakerMigrate(self, *args, **kwargs)
        hyperlinkMigrate(self, *args, **kwargs)
        documentMigrate(self, *args, **kwargs)
        groupingMigrate(self, *args, **kwargs)
        # Les tables Ze4fg_collections et Ze4fg_collection_categories sont
        # inutilisées sur cette instance WebTV (les vraies données se trouvent dans
        # Ze4fg_vdogrouping, déjà migrée par groupingMigrate ci-dessus), mais ce code
        # exécute tout de même cette migration au cas où un autre environnement les utiliserait.
        collectionMigrate(self, *args, **kwargs)
        commentMigrate(self, *args, **kwargs)


# Essayer d'abord avec une petite limite. J'ai testé sans limite et la migration
# complète a pris environ 20 minutes

# Aussi, chaque fichier src/apps/migration/utils/...Migrate.py contient des explications et des
# remarques importantes dans les commentaires en haut du fichier.

# Ça peut aider pour comprendre le fonctionnement ou effectuer des modifications
# si besoin.

# Exemple : les collections côté WebTV peuvent être multiples alors que Pod ne
# permet qu'une seule collection. -> la on conserve uniquement la première.

# pour tester: make enter puis Python3 manage.py Explosion
