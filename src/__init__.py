"""
OpenMediaTrust - Enterprise C2PA Manifest System

A comprehensive solution for creating, managing, and verifying C2PA manifests
with post-quantum cryptography support.
"""

__version__ = "1.0.0"
__author__ = "OpenMediaTrust Team"

from src.core.manifest_creator import ManifestCreator
from src.core.signer import Signer
from src.verification.validator import ManifestValidator

__all__ = ["ManifestCreator", "Signer", "ManifestValidator"]
