from django.core.management.base import BaseCommand

from src.apps.migration.utils.userMigrate import userMigrate
from src.apps.migration.utils.videoMigrate import videoMigrate
#from src.apps.migration.utils.speakerMigrate import speakerMigrate
#from src.apps.migration.utils.commentMigrate import commentMigrate
#from src.apps.migration.utils.hyperlinkMigrate import hyperlinkMigrate
#from src.apps.migration.utils.collectionMigrate import collectionMigrate

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Nombre de vidéos à migrer (défaut: 10, 0 = toutes)",
        )

    def handle(self, *args, **kwargs):
        userMigrate(self, *args, **kwargs) #Normalement bon
        videoMigrate(self, *args, **kwargs) #Normalement bon
        #commentMigrate(self, *args, **kwargs) #verifier et avoir des données AVANT D'UTILISER
        #speakerMigrate(self, *args, **kwargs) #FINIR/VERIFIER AVANT D'UTILISER
        #hyperlinkMigrate(self, *args, **kwargs) #Normalement bon

        #collectionMigrate(self, *args, **kwargs) #FAIRE/FINIR AVANT D'UTILISER --> pas du tout fonctionnel/correct