# import json


from . import ActivityPubTestCase


class VideoDiscoveryTest(ActivityPubTestCase):
    def test_video_deserialization(self):
        """Test ExternalVideo creation from a AP Video."""
        # with open("pod/activitypub/tests/fixtures/peertube_video.json") as fd:
        #     payload = json.load(fd)

        # video = ap_video_to_external_video(payload)

        # assert (
        #    video.ap_id
        #    == "http://peertube.test/videos/watch/dc6d7e53-9acc-45ca-ac3e-adac05c4bb77"
        # )

        # TODO: implement the rest of the test
