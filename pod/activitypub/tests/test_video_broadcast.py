from unittest.mock import patch

from . import ActivityPubTestCase


class VideoBroadcastTest(ActivityPubTestCase):
    @patch("pod.activitypub.tasks.task_broadcast_local_video_deletion.delay")
    @patch("pod.activitypub.tasks.task_broadcast_local_video_update.delay")
    @patch("pod.activitypub.tasks.task_broadcast_local_video_creation.delay")
    def test_video_creation(self, create_task, update_task, delete_task):
        """Create video and check broadcast through ActivityPub.

        Newly visible video should send a create task.
        """
        self.draft_video.save()
        assert not self.draft_video.is_visible()
        assert not self.visible_video.is_activity_pub_broadcasted
        self.draft_video.is_draft = False
        with self.captureOnCommitCallbacks(execute=True):
            self.draft_video.save()
        assert self.draft_video.is_visible()

        create_task.assert_called_with(self.draft_video.id)
        assert not update_task.called
        assert not delete_task.called

    @patch("pod.activitypub.tasks.task_broadcast_local_video_deletion.delay")
    @patch("pod.activitypub.tasks.task_broadcast_local_video_update.delay")
    @patch("pod.activitypub.tasks.task_broadcast_local_video_creation.delay")
    def test_video_update(self, create_task, update_task, delete_task):
        """Update video and check broadcast through ActivityPub.

        Visible video update should send an update task.
        """
        self.visible_video.save()
        assert self.visible_video.is_visible()
        assert self.visible_video.is_activity_pub_broadcasted
        self.visible_video.title = "Still visible video"
        with self.captureOnCommitCallbacks(execute=True):
            self.visible_video.save()

        assert not create_task.called
        update_task.assert_called_with(self.visible_video.id)
        assert not delete_task.called

    @patch("pod.activitypub.tasks.task_broadcast_local_video_deletion.delay")
    @patch("pod.activitypub.tasks.task_broadcast_local_video_update.delay")
    @patch("pod.activitypub.tasks.task_broadcast_local_video_creation.delay")
    def test_video_delete(self, create_task, update_task, delete_task):
        """Hide video and check broadcast through ActivityPub.

        Newly invisible video should send a delete task.
        """
        self.visible_video.save()
        assert self.visible_video.is_visible()
        assert self.visible_video.is_activity_pub_broadcasted
        self.visible_video.is_draft = True
        with self.captureOnCommitCallbacks(execute=True):
            self.visible_video.save()

        assert not create_task.called
        assert not update_task.called
        delete_task.assert_called_with(
            video_id=self.visible_video.id, owner_username=self.admin_user.username
        )
