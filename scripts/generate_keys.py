#!/usr/bin/env python3
"""
Key generation script for quantum-safe cryptography.

Generates ML-DSA (Dilithium) or SLH-DSA (SPHINCS+) keypairs.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.signer import KeyGenerator


def main():
    """Generate cryptographic keys."""
    parser = argparse.ArgumentParser(description="Generate quantum-safe keys")
    parser.add_argument(
        "--algorithm",
        choices=["rsa", "ml-dsa", "slh-dsa"],
        default="ml-dsa",
        help="Key algorithm (default: ml-dsa)",
    )
    parser.add_argument(
        "--output", default="keys/", help="Output directory (default: keys/)"
    )
    parser.add_argument("--key-size", type=int, default=4096, help="RSA key size")

    args = parser.parse_args()

    print("OpenMediaTrust - Key Generation")
    print("=" * 60)
    print(f"\nAlgorithm: {args.algorithm}")
    print(f"Output directory: {args.output}")

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate keys
    if args.algorithm == "rsa":
        print(f"\nGenerating RSA-{args.key_size} keypair...")
        private_key, public_key = KeyGenerator.generate_rsa_keypair(args.key_size)

        private_path = output_dir / "rsa-private.pem"
        public_path = output_dir / "rsa-public.pem"

    elif args.algorithm == "ml-dsa":
        print("\nGenerating ML-DSA (Dilithium) keypair...")
        private_key, public_key = KeyGenerator.generate_ml_dsa_keypair()

        private_path = output_dir / "ml-dsa-private.pem"
        public_path = output_dir / "ml-dsa-public.pem"

    else:
        print(f"\nAlgorithm {args.algorithm} not fully implemented yet.")
        print("This is a demonstration implementation.")
        return

    # Save keys
    KeyGenerator.save_key(private_key, str(private_path))
    KeyGenerator.save_key(public_key, str(public_path))

    print(f"\n✓ Keys generated successfully")
    print(f"  Private key: {private_path}")
    print(f"  Public key: {public_path}")

    print("\n⚠️  IMPORTANT: Keep your private key secure!")
    print("   - Store in HSM for production use")
    print("   - Set appropriate file permissions")
    print("   - Never commit to version control")

    # Set restrictive permissions
    private_path.chmod(0o600)
    print(f"\n✓ Set private key permissions to 600")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
