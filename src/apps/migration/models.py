# src/apps/migration/models.py
from django.db import models

class UserMapping(models.Model):
    old_id   = models.IntegerField(unique=True, help_text="ID dans l'ancienne BDD webtv")
    new_id   = models.IntegerField(unique=True, help_text="ID dans la nouvelle BDD pod")
    username = models.CharField(max_length=150)

    class Meta:
        verbose_name = "User Mapping"

    def __str__(self):
        return f"{self.username}: {self.old_id} → {self.new_id}"


class VideoMapping(models.Model):
    old_id = models.IntegerField(unique=True, help_text="ID dans l'ancienne BDD webtv")
    new_id = models.IntegerField(unique=True, help_text="ID dans la nouvelle BDD pod")

    class Meta:
        verbose_name = "Video Mapping"

    def __str__(self):
        return f"{self.old_id} → {self.new_id}"


#Verifier les migrates de tout ce qu'il y a en dessous --> normalement fonctionnel mais pas sure car manque de données pour test et/ou pas pret dans podV5 au moment de l'ecriture des scripts.  
"""
class CommentMapping(models.Model):
    old_id = models.IntegerField(unique=True, help_text="ID dans l'ancienne BDD webtv")
    new_id = models.IntegerField(unique=True, help_text="ID dans la nouvelle BDD pod")

    class Meta:
        verbose_name = "Comment Mapping"

    def __str__(self):
        return f"{self.old_id} → {self.new_id}"
"""
    
        
"""
class HyperlinkMapping(models.Model):
    old_id = models.IntegerField(unique=True, help_text="ID dans l'ancienne BDD webtv")
    new_id = models.IntegerField(unique=True, help_text="ID dans la nouvelle BDD pod")

    class Meta:
        verbose_name = "Hyperlink Mapping"

    def __str__(self):
        return f"{self.old_id} → {self.new_id}"
"""

"""
class SpeakerMapping(models.Model):
    old_id = models.IntegerField(unique=True, help_text="ID dans l'ancienne BDD webtv")
    new_id = models.IntegerField(unique=True, help_text="ID dans la nouvelle BDD pod")

    class Meta:
        verbose_name = "Speaker Mapping"

    def __str__(self):
        return f"{self.old_id} → {self.new_id}"
"""


"""
collectionMappings:
"""

class ChannelMapping(models.Model):
    old_id = models.IntegerField(unique=True, db_index=True)
    new_id = models.IntegerField()

    class Meta:
        verbose_name = "Channel Mapping"
        verbose_name_plural = "Channel Mappings"

    def __str__(self):
        return f"Channel {self.old_id} → {self.new_id}"


class PlaylistMapping(models.Model):
    old_id = models.IntegerField(unique=True, db_index=True)
    new_id = models.IntegerField()

    class Meta:
        verbose_name = "Playlist Mapping"
        verbose_name_plural = "Playlist Mappings"

    def __str__(self):
        return f"Playlist {self.old_id} → {self.new_id}"


class ThemeMapping(models.Model):
    old_id = models.IntegerField(unique=True, db_index=True)
    new_id = models.IntegerField()

    class Meta:
        verbose_name = "Theme Mapping"
        verbose_name_plural = "Theme Mappings"

    def __str__(self):
        return f"Theme {self.old_id} → {self.new_id}"