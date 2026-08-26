# src/apps/migration/models.py
from django.db import models


class UserMapping(models.Model):
    old_id = models.IntegerField(unique=True, help_text="ID dans l'ancienne BDD webtv")
    new_id = models.IntegerField(unique=True, help_text="ID dans la nouvelle BDD pod")
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


class CommentMapping(models.Model):
    old_id = models.IntegerField(unique=True, help_text="ID dans l'ancienne BDD webtv")
    new_id = models.IntegerField(unique=True, help_text="ID dans la nouvelle BDD pod")

    class Meta:
        verbose_name = "Comment Mapping"

    def __str__(self):
        return f"{self.old_id} → {self.new_id}"


class CompletionMapping(models.Model):
    """
    Speaker mapping webtv
    """

    old_id = models.IntegerField(unique=True, help_text="ID dans l'ancienne BDD webtv")
    new_id = models.IntegerField(unique=True, help_text="ID dans la nouvelle BDD pod")

    class Meta:
        verbose_name = "Completion Mapping"

    def __str__(self):
        return f"{self.old_id} → {self.new_id}"


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


class GroupingMapping(models.Model):
    """
    Mapping for Ze4fg_vdogrouping rows (webtv's real Collection/Thematique
    data). Kept separate from ChannelMapping/ThemeMapping, which are reserved
    for the (currently empty) Ze4fg_collections/Ze4fg_collection_categories
    old_id namespace, to avoid old_id collisions between the two sources.
    """

    TARGET_CHANNEL = "channel"
    TARGET_THEME = "theme"
    TARGET_CHOICES = [
        (TARGET_CHANNEL, "Channel"),
        (TARGET_THEME, "Theme"),
    ]

    old_id = models.IntegerField(unique=True, db_index=True)
    new_id = models.IntegerField()
    target_type = models.CharField(max_length=10, choices=TARGET_CHOICES)

    class Meta:
        verbose_name = "Grouping Mapping"
        verbose_name_plural = "Grouping Mappings"

    def __str__(self):
        return f"Grouping {self.old_id} → {self.target_type}:{self.new_id}"


class DocumentMapping(models.Model):
    """
    Mapping for Ze4fg_video_documents rows. old_id is the video_documents
    join row id (not Ze4fg_documents.id), since a single webtv document can
    be attached to several videos while completion.Document requires exactly
    one video per row — each (video, document) pair becomes its own Document.
    """

    old_id = models.IntegerField(unique=True, db_index=True)
    new_id = models.IntegerField()

    class Meta:
        verbose_name = "Document Mapping"
        verbose_name_plural = "Document Mappings"

    def __str__(self):
        return f"Document {self.old_id} → {self.new_id}"
