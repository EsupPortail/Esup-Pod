from Crypto.PublicKey import RSA

from pod.activitypub.signature import (
    build_signature_headers,
    build_signature_payload,
    check_signature_headers,
    check_signature_payload,
)

from . import ActivityPubTestCase


class ActivityPubViewTest(ActivityPubTestCase):
    def setUp(self):
        super().setUp()

        self.ap_key_1 = RSA.generate(2048)
        self.ap_key_2 = RSA.generate(2048)
        self.pk1 = self.ap_key_1.export_key().decode()
        self.pk2 = self.ap_key_2.export_key().decode()
        self.pub1 = self.ap_key_1.publickey().export_key().decode()
        self.pub2 = self.ap_key_2.publickey().export_key().decode()

    def test_signature_payload(self):
        priv_key = RSA.import_key(self.pk1)
        valid_pub_key = RSA.import_key(self.pub1)
        invalid_pub_key = RSA.import_key(self.pub2)

        payload = {"foo": "bar", "actor": "baz"}
        payload["signature"] = build_signature_payload(priv_key, payload)

        self.assertTrue(check_signature_payload(valid_pub_key, payload))
        self.assertFalse(check_signature_payload(invalid_pub_key, payload))

    def test_signature_headers(self):
        priv_key = RSA.import_key(self.pk1)
        valid_pub_key = RSA.import_key(self.pub1)
        invalid_pub_key = RSA.import_key(self.pub2)

        payload = {"foo": "bar", "actor": "baz"}
        url = "https://ap.test"
        public_key_url = "https://ap.test/yolo"
        headers = build_signature_headers(priv_key, public_key_url, payload, url)

        self.assertTrue(check_signature_headers(valid_pub_key, payload, headers, url))
        self.assertFalse(
            check_signature_headers(invalid_pub_key, payload, headers, url)
        )
