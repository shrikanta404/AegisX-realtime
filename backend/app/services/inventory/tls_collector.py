import socket
import ssl
from datetime import datetime, timezone
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes


class TLSCollector:
    """
    Collect current TLS certificate metadata for an authorized hostname.

    Certificate verification is intentionally disabled for the observation
    handshake so expired or otherwise invalid certificates can still be
    inspected and reported. This collector only retrieves certificate metadata;
    it does not exploit or alter the target.
    """

    def collect(self, domain: str, port: int = 443) -> dict[str, Any]:
        domain = domain.strip().lower().rstrip(".")

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with socket.create_connection((domain, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as tls_socket:
                der_certificate = tls_socket.getpeercert(binary_form=True)
                if not der_certificate:
                    raise RuntimeError("No TLS certificate was returned.")

                certificate = x509.load_der_x509_certificate(der_certificate)
                fingerprint = certificate.fingerprint(hashes.SHA256()).hex()

                return {
                    "subject": certificate.subject.rfc4514_string() or None,
                    "issuer": certificate.issuer.rfc4514_string() or None,
                    "serial_number": format(certificate.serial_number, "x"),
                    "valid_from": self._certificate_not_before(certificate),
                    "valid_until": self._certificate_not_after(certificate),
                    "fingerprint": fingerprint,
                    "tls_version": tls_socket.version(),
                    "cipher": tls_socket.cipher()[0] if tls_socket.cipher() else None,
                    "is_expired": certificate.not_valid_after_utc < datetime.now(timezone.utc),
                }

    @staticmethod
    def _certificate_not_before(certificate: x509.Certificate) -> datetime:
        # cryptography >= 42 exposes timezone-aware properties.
        value = getattr(certificate, "not_valid_before_utc", None)
        if value is not None:
            return value
        return certificate.not_valid_before.replace(tzinfo=timezone.utc)

    @staticmethod
    def _certificate_not_after(certificate: x509.Certificate) -> datetime:
        value = getattr(certificate, "not_valid_after_utc", None)
        if value is not None:
            return value
        return certificate.not_valid_after.replace(tzinfo=timezone.utc)
