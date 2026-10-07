"""Esup-Pod test-only fixtures for remote import validation."""

import ipaddress


class SimulatedPublicIPv4Address(ipaddress.IPv4Address):
    """Use a documentation address (RFC 5737) as a simulated public destination."""

    @property
    def is_global(self) -> bool:
        """Exercise public-host validation without referencing a real server."""
        return True
