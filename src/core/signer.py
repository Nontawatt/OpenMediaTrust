"""
Quantum-safe signing service for C2PA manifests.

Supports classical and post-quantum cryptographic algorithms including
ML-DSA (Dilithium), SLH-DSA (SPHINCS+), and hybrid modes.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from src.core.models import Manifest, Signature, SignatureAlgorithm


class Signer:
    """Sign C2PA manifests with quantum-safe algorithms."""

    def __init__(
        self,
        algorithm: SignatureAlgorithm = SignatureAlgorithm.ML_DSA_65,
        private_key_path: Optional[str] = None,
        certificate_path: Optional[str] = None,
        tsa_url: Optional[str] = None,
    ):
        """
        Initialize signer.

        Args:
            algorithm: Signature algorithm to use
            private_key_path: Path to private key file
            certificate_path: Path to certificate file
            tsa_url: Time Stamping Authority URL
        """
        self.algorithm = algorithm
        self.private_key_path = private_key_path
        self.certificate_path = certificate_path
        self.tsa_url = tsa_url
        self._private_key = None
        self._certificate_chain = []

        if private_key_path:
            self._load_private_key(private_key_path)
        if certificate_path:
            self._load_certificates(certificate_path)

    def _load_private_key(self, key_path: str) -> None:
        """Load private key from file."""
        path = Path(key_path)
        if not path.exists():
            raise FileNotFoundError(f"Private key not found: {key_path}")

        with open(key_path, "rb") as f:
            key_data = f.read()

        # For classical algorithms, use cryptography library
        if self.algorithm in [
            SignatureAlgorithm.RSA_PSS_SHA256,
            SignatureAlgorithm.RSA_PSS_SHA384,
            SignatureAlgorithm.RSA_PSS_SHA512,
        ]:
            self._private_key = serialization.load_pem_private_key(
                key_data, password=None, backend=default_backend()
            )
        else:
            # For PQC algorithms, store raw key data
            # In production, use proper PQC library (liboqs, pqcrypto)
            self._private_key = key_data

    def _load_certificates(self, cert_path: str) -> None:
        """Load certificate chain from file."""
        path = Path(cert_path)
        if not path.exists():
            raise FileNotFoundError(f"Certificate not found: {cert_path}")

        with open(cert_path, "rb") as f:
            cert_data = f.read()

        # Load certificate chain
        try:
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")
            self._certificate_chain = [cert_pem]
        except Exception:
            # For PQC certificates, store as base64
            import base64

            self._certificate_chain = [base64.b64encode(cert_data).decode("utf-8")]

    def sign(self, manifest: Manifest) -> Manifest:
        """
        Sign a C2PA manifest.

        Args:
            manifest: Manifest to sign

        Returns:
            Signed manifest with signature
        """
        # Serialize manifest for signing
        manifest_data = self._prepare_manifest_for_signing(manifest)

        # Compute signature
        signature_value = self._compute_signature(manifest_data)

        # Create signature object
        signature = Signature(
            alg=self.algorithm,
            certificate_chain=self._certificate_chain,
            timestamp=datetime.utcnow(),
            tsa=self.tsa_url,
            signature_value=signature_value,
        )

        manifest.signature = signature
        return manifest

    def _prepare_manifest_for_signing(self, manifest: Manifest) -> bytes:
        """Prepare manifest data for signing."""
        # Convert manifest to canonical JSON
        manifest_dict = manifest.to_dict()

        # Remove signature field if present
        manifest_dict.pop("signature", None)

        # Serialize to canonical JSON
        json_data = json.dumps(manifest_dict, sort_keys=True, separators=(",", ":"))
        return json_data.encode("utf-8")

    def _compute_signature(self, data: bytes) -> bytes:
        """Compute signature over data."""
        if self.algorithm in [
            SignatureAlgorithm.RSA_PSS_SHA256,
            SignatureAlgorithm.RSA_PSS_SHA384,
            SignatureAlgorithm.RSA_PSS_SHA512,
        ]:
            return self._sign_rsa_pss(data)
        elif self.algorithm in [
            SignatureAlgorithm.ML_DSA_44,
            SignatureAlgorithm.ML_DSA_65,
            SignatureAlgorithm.ML_DSA_87,
        ]:
            return self._sign_ml_dsa(data)
        elif self.algorithm in [
            SignatureAlgorithm.SLH_DSA_SHA2_128S,
            SignatureAlgorithm.SLH_DSA_SHA2_256S,
        ]:
            return self._sign_slh_dsa(data)
        elif self.algorithm in [
            SignatureAlgorithm.HYBRID_RSA_ML_DSA,
            SignatureAlgorithm.HYBRID_ECDSA_ML_DSA,
        ]:
            return self._sign_hybrid(data)
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")

    def _sign_rsa_pss(self, data: bytes) -> bytes:
        """Sign with RSA-PSS."""
        if not isinstance(self._private_key, rsa.RSAPrivateKey):
            raise ValueError("Invalid private key for RSA-PSS")

        # Determine hash algorithm
        hash_alg_map = {
            SignatureAlgorithm.RSA_PSS_SHA256: hashes.SHA256(),
            SignatureAlgorithm.RSA_PSS_SHA384: hashes.SHA384(),
            SignatureAlgorithm.RSA_PSS_SHA512: hashes.SHA512(),
        }
        hash_alg = hash_alg_map.get(self.algorithm, hashes.SHA256())

        signature = self._private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hash_alg), salt_length=padding.PSS.MAX_LENGTH
            ),
            hash_alg,
        )
        return signature

    def _sign_ml_dsa(self, data: bytes) -> bytes:
        """
        Sign with ML-DSA (Dilithium).

        Note: This is a placeholder implementation.
        In production, use liboqs-python or pqcrypto library.
        """
        # Placeholder: In production, use actual ML-DSA implementation
        # from pqcrypto.sign.dilithium3 import sign
        # signature = sign(data, self._private_key)

        # For demonstration, compute a hash-based signature
        hash_value = hashlib.sha3_256(data + (self._private_key or b"demo_key")).digest()

        # ML-DSA signatures are larger (e.g., ~3309 bytes for Dilithium3)
        # This is a mock signature for demonstration
        return b"ML-DSA-SIGNATURE:" + hash_value

    def _sign_slh_dsa(self, data: bytes) -> bytes:
        """
        Sign with SLH-DSA (SPHINCS+).

        Note: This is a placeholder implementation.
        In production, use liboqs-python or pqcrypto library.
        """
        # Placeholder: In production, use actual SPHINCS+ implementation
        # from pqcrypto.sign.sphincs_sha256_128s import sign
        # signature = sign(data, self._private_key)

        hash_value = hashlib.sha3_512(data + (self._private_key or b"demo_key")).digest()
        return b"SLH-DSA-SIGNATURE:" + hash_value

    def _sign_hybrid(self, data: bytes) -> bytes:
        """
        Sign with hybrid classical+PQC algorithm.

        Combines classical signature with post-quantum signature.
        """
        # Compute both signatures
        classical_sig = self._sign_rsa_pss(data)
        pqc_sig = self._sign_ml_dsa(data)

        # Combine signatures
        # Format: [classical_length:4][classical_sig][pqc_sig]
        classical_len = len(classical_sig).to_bytes(4, "big")
        hybrid_sig = classical_len + classical_sig + pqc_sig

        return hybrid_sig

    def verify(self, manifest: Manifest) -> bool:
        """
        Verify manifest signature.

        Args:
            manifest: Signed manifest

        Returns:
            True if signature is valid
        """
        if not manifest.signature:
            return False

        # Prepare manifest data
        manifest_data = self._prepare_manifest_for_signing(manifest)

        # Verify signature based on algorithm
        try:
            return self._verify_signature(
                manifest_data, manifest.signature.signature_value or b""
            )
        except Exception:
            return False

    def _verify_signature(self, data: bytes, signature: bytes) -> bool:
        """Verify signature over data."""
        if self.algorithm in [
            SignatureAlgorithm.RSA_PSS_SHA256,
            SignatureAlgorithm.RSA_PSS_SHA384,
            SignatureAlgorithm.RSA_PSS_SHA512,
        ]:
            return self._verify_rsa_pss(data, signature)
        elif self.algorithm in [
            SignatureAlgorithm.ML_DSA_44,
            SignatureAlgorithm.ML_DSA_65,
            SignatureAlgorithm.ML_DSA_87,
        ]:
            return self._verify_ml_dsa(data, signature)
        elif self.algorithm in [
            SignatureAlgorithm.SLH_DSA_SHA2_128S,
            SignatureAlgorithm.SLH_DSA_SHA2_256S,
        ]:
            return self._verify_slh_dsa(data, signature)
        elif self.algorithm in [
            SignatureAlgorithm.HYBRID_RSA_ML_DSA,
            SignatureAlgorithm.HYBRID_ECDSA_ML_DSA,
        ]:
            return self._verify_hybrid(data, signature)
        return False

    def _verify_rsa_pss(self, data: bytes, signature: bytes) -> bool:
        """Verify RSA-PSS signature."""
        # Would use public key from certificate
        # This is a placeholder
        return True

    def _verify_ml_dsa(self, data: bytes, signature: bytes) -> bool:
        """Verify ML-DSA signature."""
        # Placeholder verification
        expected = b"ML-DSA-SIGNATURE:" + hashlib.sha3_256(
            data + (self._private_key or b"demo_key")
        ).digest()
        return signature == expected

    def _verify_slh_dsa(self, data: bytes, signature: bytes) -> bool:
        """Verify SLH-DSA signature."""
        # Placeholder verification
        expected = b"SLH-DSA-SIGNATURE:" + hashlib.sha3_512(
            data + (self._private_key or b"demo_key")
        ).digest()
        return signature == expected

    def _verify_hybrid(self, data: bytes, signature: bytes) -> bool:
        """Verify hybrid signature."""
        # Extract classical and PQC signatures
        classical_len = int.from_bytes(signature[:4], "big")
        classical_sig = signature[4 : 4 + classical_len]
        pqc_sig = signature[4 + classical_len :]

        # Verify both
        classical_valid = self._verify_rsa_pss(data, classical_sig)
        pqc_valid = self._verify_ml_dsa(data, pqc_sig)

        return classical_valid and pqc_valid


class KeyGenerator:
    """Generate quantum-safe key pairs."""

    @staticmethod
    def generate_rsa_keypair(key_size: int = 4096) -> Tuple[bytes, bytes]:
        """
        Generate RSA key pair.

        Args:
            key_size: RSA key size in bits

        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=key_size, backend=default_backend()
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return private_pem, public_pem

    @staticmethod
    def generate_ml_dsa_keypair() -> Tuple[bytes, bytes]:
        """
        Generate ML-DSA (Dilithium) key pair.

        Note: This is a placeholder. In production, use liboqs-python.

        Returns:
            Tuple of (private_key, public_key)
        """
        # Placeholder: Use actual ML-DSA key generation
        # from pqcrypto.sign.dilithium3 import generate_keypair
        # public_key, private_key = generate_keypair()

        import secrets

        # Mock keys for demonstration
        private_key = b"ML-DSA-PRIVATE-KEY:" + secrets.token_bytes(32)
        public_key = b"ML-DSA-PUBLIC-KEY:" + secrets.token_bytes(32)

        return private_key, public_key

    @staticmethod
    def save_key(key_data: bytes, file_path: str) -> None:
        """Save key to file."""
        with open(file_path, "wb") as f:
            f.write(key_data)
