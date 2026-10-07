"""Esup-Pod HTTPS import tests using a local TLS server and a test-only key."""

import ipaddress
import ssl
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from unittest.mock import patch

import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from django.test import SimpleTestCase
from urllib3.util.connection import create_connection

from pod.import_video.tests.helpers import SimulatedPublicIPv4Address
from pod.import_video.utils import PinnedIPAdapter, safe_request


def create_test_certificate(directory):
    """Generate an ephemeral self-signed certificate with a domain-only SAN."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "bbb.example.test")])
    now = datetime.now(timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("bbb.example.test")]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    certificate_path = Path(directory) / "certificate.pem"
    key_path = Path(directory) / "key.pem"
    certificate_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return str(certificate_path), str(key_path)


class RecordingRequestHandler(BaseHTTPRequestHandler):
    """Serve a BBB-like page and expose received headers to the tests."""

    def do_GET(self):
        """Return the recording page, its session cookie, or a redirect."""
        self.server.request_headers.append(dict(self.headers))
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/playback/video/recording/")
            self.end_headers()
            return
        content = b'<video><source src="video-0.m4v"></video>'
        self.send_response(200)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Set-Cookie", "bbb_session=recording; Path=/; Secure")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        """Keep HTTP server logs out of the test output."""


class RemoteImportHTTPSTest(SimpleTestCase):
    """Verify real TLS, IP pinning, BBB cookies, and streamed responses."""

    @classmethod
    def setUpClass(cls):
        """Start a local HTTPS server with a certificate for bbb.example.test."""
        super().setUpClass()
        directory = TemporaryDirectory()
        cls.addClassCleanup(directory.cleanup)
        cls.certificate, key_path = create_test_certificate(directory.name)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cls.certificate, key_path)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), RecordingRequestHandler)
        cls.addClassCleanup(cls.server.server_close)
        cls.server.server_names = []
        cls.server.request_headers = []
        context.set_servername_callback(
            lambda connection, hostname, ssl_context: cls.server.server_names.append(
                hostname
            )
        )
        cls.server.socket = context.wrap_socket(cls.server.socket, server_side=True)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.addClassCleanup(cls.thread.join)
        cls.addClassCleanup(cls.server.shutdown)

    def setUp(self):
        """Simulate a public IP with a documentation address routed locally."""
        self.server.server_names.clear()
        self.server.request_headers.clear()
        self.connection_addresses = []
        self.address = SimulatedPublicIPv4Address("192.0.2.1")
        self.source_url = (
            f"https://bbb.example.test:{self.server.server_port}"
            "/playback/video/recording/"
        )
        self.session = requests.Session()
        self.session.trust_env = False
        self.addCleanup(self.session.close)
        self.resolver = self.enterContext(
            patch(
                "pod.import_video.utils._resolve_remote_addresses",
                return_value={self.address},
            )
        )
        self.enterContext(
            patch(
                "urllib3.util.connection.create_connection",
                side_effect=self.connect_locally,
            )
        )

    def connect_locally(self, address, *args, **kwargs):
        """Record the requested destination and route the socket to the test server."""
        self.connection_addresses.append(address)
        return create_connection(self.server.server_address, *args, **kwargs)

    def test_https_uses_original_hostname_and_validated_ip(self):
        """A domain certificate must work when the TCP destination is pinned."""
        original_adapters = self.session.adapters
        with safe_request(
            "get",
            self.source_url,
            session=self.session,
            verify=self.certificate,
            timeout=2,
            headers={"X-Import-Test": "BBB"},
        ) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.url, self.source_url)
        self.assertEqual(self.server.server_names, ["bbb.example.test"])
        self.assertEqual(
            self.connection_addresses,
            [(str(self.address), self.server.server_port)],
        )
        self.assertEqual(
            self.server.request_headers[0]["Host"],
            f"bbb.example.test:{self.server.server_port}",
        )
        self.assertEqual(self.server.request_headers[0]["X-Import-Test"], "BBB")
        self.assertIs(self.session.adapters, original_adapters)

    def test_https_rejects_certificate_for_another_hostname(self):
        """Trusting the certificate must not disable hostname verification."""
        original_adapters = self.session.adapters
        with self.assertRaises(requests.exceptions.SSLError):
            safe_request(
                "get",
                self.source_url.replace("bbb.example.test", "other.example.test"),
                session=self.session,
                verify=self.certificate,
                timeout=2,
            )
        self.assertEqual(self.server.server_names, ["other.example.test"])
        self.assertEqual(self.server.request_headers, [])
        self.assertIs(self.session.adapters, original_adapters)

    def test_https_rejects_untrusted_certificate(self):
        """Certificate chain verification remains enabled by default."""
        with self.assertRaises(requests.exceptions.SSLError):
            safe_request("get", self.source_url, session=self.session, timeout=2)
        self.assertEqual(self.server.request_headers, [])

    def test_https_preserves_bbb_session_cookie(self):
        """A cookie obtained while parsing BBB must reach the video download."""
        with safe_request(
            "get",
            self.source_url,
            session=self.session,
            verify=self.certificate,
            timeout=2,
        ):
            pass
        with safe_request(
            "get",
            self.source_url + "video-0.m4v",
            session=self.session,
            verify=self.certificate,
            timeout=2,
        ):
            pass
        self.assertEqual(
            self.server.request_headers[1].get("Cookie"), "bbb_session=recording"
        )

    def test_https_stream_remains_readable(self):
        """Adapter cleanup must not close an in-progress video download."""
        with safe_request(
            "get",
            self.source_url,
            session=self.session,
            verify=self.certificate,
            timeout=2,
            stream=True,
        ) as response:
            self.assertIn(b"video-0.m4v", response.raw.read())

    def test_https_stream_without_session_remains_readable(self):
        """An internally owned session can return a stream after its cleanup."""
        with patch("pod.import_video.utils.Session", return_value=self.session):
            with safe_request(
                "get", self.source_url, verify=self.certificate, timeout=2, stream=True
            ) as response:
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"video-0.m4v", response.raw.read())

    def test_https_redirect_revalidates_destination(self):
        """Follow a relative redirect while revalidating the public host."""
        with safe_request(
            "get",
            self.source_url.replace("/playback/video/recording/", "/redirect"),
            session=self.session,
            verify=self.certificate,
            timeout=2,
        ) as response:
            self.assertEqual(response.url, self.source_url)
        self.assertEqual(self.resolver.call_count, 2)
        self.assertEqual(self.server.server_names, ["bbb.example.test"] * 2)


class PinnedIPAdapterTest(SimpleTestCase):
    """Cover IPv6 destinations and HTTP proxy forwarding without network access."""

    def test_https_ipv6_preserves_hostname_and_tls_verification(self):
        """Only the connection host changes for an IPv6 destination."""
        address = ipaddress.ip_address("2001:db8::1")  # RFC 3849 documentation range.
        adapter = PinnedIPAdapter(address)
        self.addCleanup(adapter.close)
        request = requests.Request(
            "GET", "https://bbb.example.test:8443/video/"
        ).prepare()
        pool = adapter.get_connection_with_tls_context(request, verify=True)
        self.assertEqual(pool.host, str(address))
        self.assertEqual(pool.port, 8443)
        self.assertEqual(pool.assert_hostname, "bbb.example.test")
        self.assertEqual(pool.conn_kw["server_hostname"], "bbb.example.test")
        self.assertEqual(pool.cert_reqs, "CERT_REQUIRED")

    def test_http_proxy_uses_validated_ip_and_original_port(self):
        """An HTTP forwarding proxy must not resolve the original hostname again."""
        proxies = {"http": "http://proxy.example.test:3128"}
        for address, expected_host in (
            ("192.0.2.1", "192.0.2.1"),
            ("2001:db8::1", "[2001:db8::1]"),
        ):
            with self.subTest(address=address):
                adapter = PinnedIPAdapter(ipaddress.ip_address(address))
                self.addCleanup(adapter.close)
                request = requests.Request(
                    "GET", "http://bbb.example.test:8080/video/?download=1"
                ).prepare()
                self.assertEqual(
                    adapter.request_url(request, proxies),
                    f"http://{expected_host}:8080/video/?download=1",
                )

    def test_https_proxy_pins_tunnel_and_preserves_tls_hostname(self):
        """An HTTPS import through a proxy uses the validated tunnel destination."""
        adapter = PinnedIPAdapter(ipaddress.ip_address("192.0.2.1"))
        self.addCleanup(adapter.close)
        request = requests.Request("GET", "https://bbb.example.test/video/").prepare()
        proxies = {"https": "http://proxy.example.test:3128"}
        pool = adapter.get_connection_with_tls_context(
            request, verify=True, proxies=proxies
        )
        self.assertEqual(pool.host, "192.0.2.1")
        self.assertEqual(pool.assert_hostname, "bbb.example.test")
        self.assertEqual(pool.conn_kw["server_hostname"], "bbb.example.test")
        self.assertEqual(adapter.request_url(request, proxies), "/video/")
