import base64
import datetime
import email.utils
import json
from typing import Dict
from urllib.parse import urlparse

from Crypto.Hash import SHA256
from Crypto.PublicKey.RSA import RsaKey
from Crypto.Signature import pkcs1_15
from pyld import jsonld


def payload_hash(payload):
    payload_json = json.dumps(payload) if isinstance(payload, dict) else payload
    payload_hash = SHA256.new(payload_json.encode("utf-8"))
    digest = payload_hash.digest()
    return digest


def payload_signature(private_key, string):
    to_be_signed_str_bytes = bytes(string, "utf-8")
    to_be_signed_str_hash = SHA256.new(bytes(to_be_signed_str_bytes))
    sig = pkcs1_15.new(private_key).sign(to_be_signed_str_hash)
    return sig


def payload_check(public_key, payload, signature) -> bool:
    to_be_checked_str_bytes = bytes(payload, "utf-8")
    to_be_checked_str_hash = SHA256.new(bytes(to_be_checked_str_bytes))
    verifier = pkcs1_15.new(public_key)

    try:
        verifier.verify(to_be_checked_str_hash, signature)
        return True

    except ValueError:
        return False


def payload_normalize(payload):
    return jsonld.normalize(
        payload, {"algorithm": "URDNA2015", "format": "application/n-quads"}
    )


def build_signature_headers(
    private_key: RsaKey, public_key_url: str, payload: Dict[str, str], url: str
) -> Dict[str, str]:
    """Sign JSON-LD payload according to the 'Signing HTTP Messages' RFC draft.
    This brings compatibility with peertube (and mastodon for instance).

    More information here:
        - https://datatracker.ietf.org/doc/html/draft-cavage-http-signatures-12
        - https://framacolibri.org/t/rfc9421-replaces-the-signing-http-messages-draft/20911/2
    """
    date = email.utils.formatdate(usegmt=True)
    url = urlparse(url)

    payload_hash_raw = payload_hash(payload)
    payload_hash_b64 = base64.b64encode(payload_hash_raw).decode()

    to_sign = (
        f"(request-target): post {url.path}\n"
        f"host: {url.netloc}\n"
        f"date: {date}\n"
        f"digest: SHA-256={payload_hash_b64}"
    )
    sig_raw = payload_signature(private_key, to_sign)
    sig_b64 = base64.b64encode(sig_raw).decode()

    signature_header = f'keyId="{public_key_url}",algorithm="rsa-sha256",headers="(request-target) host date digest",signature="{sig_b64}"'
    request_headers = {
        "host": url.netloc,
        "date": date,
        "digest": f"SHA-256={payload_hash_b64}",
        "content-type": "application/activity+json",
        "signature": signature_header,
    }
    return request_headers


def check_signature_headers(
    public_key: RsaKey, payload: Dict[str, str], headers: Dict[str, str], url: str
) -> bool:
    """Sign JSON-LD payload according to the 'Signing HTTP Messages' RFC draft."""

    url = urlparse(url)
    date_header = headers["date"]

    payload_hash_raw = payload_hash(payload)
    payload_hash_b64 = base64.b64encode(payload_hash_raw).decode()

    to_check = (
        f"(request-target): post {url.path}\n"
        f"host: {url.netloc}\n"
        f"date: {date_header}\n"
        f"digest: SHA-256={payload_hash_b64}"
    )

    signature_header = headers["signature"]
    signature_header_dict = dict(
        (item.split("=", maxsplit=1) for item in signature_header.split(","))
    )
    sig_b64 = signature_header_dict["signature"]
    sig_raw = base64.b64decode(sig_b64)

    is_valid = payload_check(public_key, to_check, sig_raw)
    return is_valid


def signature_payload_raw_data(payload, signature):
    """Build the raw data to be signed or checked according to the 'Linked Data Signatures 1.0' RFC draft."""

    options_payload = {
        "@context": [
            "https://w3id.org/security/v1",
            {"RsaSignature2017": "https://w3id.org/security#RsaSignature2017"},
        ],
        "creator": signature["creator"],
        "created": signature["created"],
    }
    options_normalized = payload_normalize(options_payload)
    options_hash = payload_hash(options_normalized)

    document_normalized = payload_normalize(payload)
    document_hash = payload_hash(document_normalized)

    return options_hash.hex() + document_hash.hex()


def build_signature_payload(
    private_key: RsaKey, payload: Dict[str, str]
) -> Dict[str, str]:
    """Sign JSON-LD payload according to the 'Linked Data Signatures 1.0' RFC draft.
    This brings compatibility with peertube (and mastodon for instance).

    More information here:
        - https://web.archive.org/web/20170717200644/https://w3c-dvcg.github.io/ld-signatures/
        - https://docs.joinmastodon.org/spec/security/#ld
    """

    signature = {
        "type": "RsaSignature2017",
        "creator": payload["actor"],
        "created": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
    }
    to_sign = signature_payload_raw_data(payload, signature)
    sig_raw = payload_signature(private_key, to_sign)
    sig_b64 = base64.b64encode(sig_raw).decode()
    signature["signatureValue"] = sig_b64

    return signature


def check_signature_payload(public_key: RsaKey, payload: Dict[str, str]) -> bool:
    """Check JSON-LD payload according to the 'Linked Data Signatures 1.0' RFC draft."""

    payload = dict(payload)
    signature_metadata = payload.pop("signature")
    to_check = signature_payload_raw_data(payload, signature_metadata)

    sig_b64 = signature_metadata["signatureValue"]
    sig_raw = base64.b64decode(sig_b64)

    is_valid = payload_check(public_key, to_check, sig_raw)
    return is_valid
