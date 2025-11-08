"""
Basic usage examples for OpenMediaTrust.

This script demonstrates the core functionality of creating, signing,
and verifying C2PA manifests.
"""

from pathlib import Path

from src.core.assertion_builder import AssertionBuilder
from src.core.manifest_creator import ManifestCreator
from src.core.metadata_extractor import MetadataExtractor
from src.core.models import ActionType, ClassificationLevel, DigitalSourceType
from src.core.signer import Signer, SignatureAlgorithm
from src.verification.validator import ManifestValidator


def example_1_create_basic_manifest():
    """Example 1: Create a basic manifest for an image."""
    print("Example 1: Creating basic manifest...")

    # Initialize manifest creator
    creator = ManifestCreator(
        claim_generator="MyApp/1.0",
        organization="Acme Corporation"
    )

    # Create manifest for an image
    manifest = creator.create(
        file_path="example_image.jpg",
        creator="photographer@acme.com",
        title="Product Photo - Campaign 2025",
        department="Marketing",
        project="Q4-2025-Campaign",
        classification=ClassificationLevel.PUBLIC,
        digital_source_type=DigitalSourceType.DIGITAL_CAPTURE,
    )

    print(f"✓ Manifest created: {manifest.instance_id}")
    print(f"  Title: {manifest.title}")
    print(f"  Format: {manifest.format}")
    print(f"  Assertions: {len(manifest.assertions)}")

    # Save to JSON
    creator.save_manifest(manifest, "manifest_basic.json")
    print("✓ Manifest saved to manifest_basic.json")

    return manifest


def example_2_sign_with_quantum_safe_crypto():
    """Example 2: Sign manifest with ML-DSA (Dilithium)."""
    print("\nExample 2: Signing with quantum-safe cryptography...")

    # Create a manifest
    creator = ManifestCreator()
    manifest = creator.create(
        file_path="example_image.jpg",
        creator="creator@example.com",
        title="Quantum-Safe Demo",
    )

    # Initialize signer with ML-DSA-65 (Dilithium3)
    signer = Signer(algorithm=SignatureAlgorithm.ML_DSA_65)

    # Sign the manifest
    signed_manifest = signer.sign(manifest)

    print(f"✓ Manifest signed with {signed_manifest.signature.alg.value}")
    print(f"  Timestamp: {signed_manifest.signature.timestamp}")
    print(f"  Certificate chain: {len(signed_manifest.signature.certificate_chain)} certs")

    return signed_manifest


def example_3_enterprise_workflow():
    """Example 3: Enterprise workflow with approvals."""
    print("\nExample 3: Enterprise workflow...")

    # Create manifest with workflow
    creator = ManifestCreator(organization="Enterprise Corp")
    manifest = creator.create(
        file_path="example_image.jpg",
        creator="john.doe@enterprise.com",
        title="Marketing Material",
        department="Marketing",
        classification=ClassificationLevel.PUBLIC,
    )

    print(f"✓ Manifest created with workflow")

    # Add approval step
    creator.add_approval(
        manifest=manifest,
        approver_id="jane.manager",
        approver_name="Jane Manager",
        role="approver",
        status="approved",
        comments="Looks good, approved for publication",
    )

    print("✓ Approval added to workflow")

    # Update compliance
    creator.update_compliance(
        manifest=manifest,
        pdpa_approved=True,
        trademark_cleared=True,
        legal_review="passed",
    )

    print("✓ Compliance checks updated")

    return manifest


def example_4_verify_manifest():
    """Example 4: Verify a signed manifest."""
    print("\nExample 4: Verifying manifest...")

    # Create and sign a manifest
    creator = ManifestCreator()
    manifest = creator.create(
        file_path="example_image.jpg",
        creator="creator@example.com",
        title="Verification Demo",
    )

    signer = Signer(algorithm=SignatureAlgorithm.ML_DSA_65)
    signed_manifest = signer.sign(manifest)

    # Verify the manifest
    validator = ManifestValidator()
    result = validator.validate(signed_manifest, strict=False)

    print(f"✓ Verification complete")
    print(f"  Valid: {result.valid}")
    print(f"  Trust Level: {result.trust_level.value}")
    print(f"  Signature Valid: {result.signature_valid}")
    print(f"  Assertions Verified: {len(result.assertions_verified)}")

    if result.issues:
        print(f"  Issues: {len(result.issues)}")
        for issue in result.issues:
            print(f"    - {issue.message}")

    if result.warnings:
        print(f"  Warnings: {len(result.warnings)}")
        for warning in result.warnings:
            print(f"    - {warning.message}")

    return result


def example_5_custom_assertions():
    """Example 5: Add custom assertions."""
    print("\nExample 5: Adding custom assertions...")

    creator = ManifestCreator()
    assertion_builder = AssertionBuilder()

    manifest = creator.create(
        file_path="example_image.jpg",
        creator="creator@example.com",
        title="Custom Assertions Demo",
    )

    # Add training-mining assertion (AI/ML usage control)
    training_assertion = assertion_builder.build_training_mining_assertion(
        allowed=False,
        constraint_info="This content may not be used for AI training",
    )
    creator.add_assertion(manifest, training_assertion)

    print("✓ Training-mining assertion added")

    # Add ingredient assertion (for composite content)
    creator.add_ingredient(
        manifest=manifest,
        ingredient_path="background_image.jpg",
        relationship="parentOf",
    )

    print("✓ Ingredient assertion added")
    print(f"  Total assertions: {len(manifest.assertions)}")

    return manifest


def example_6_metadata_extraction():
    """Example 6: Extract and use metadata."""
    print("\nExample 6: Metadata extraction...")

    extractor = MetadataExtractor()

    # Extract metadata
    metadata = extractor.extract("example_image.jpg")

    print("✓ Metadata extracted:")
    print(f"  File name: {metadata.get('file_name')}")
    print(f"  File size: {metadata.get('file_size')} bytes")
    print(f"  MIME type: {metadata.get('mime_type')}")

    if "width" in metadata:
        print(f"  Dimensions: {metadata['width']}x{metadata['height']}")

    if "camera_make" in metadata:
        print(f"  Camera: {metadata['camera_make']} {metadata['camera_model']}")

    if "software" in metadata:
        print(f"  Software: {metadata['software']}")

    # Extract GPS location if available
    location = extractor.extract_gps_location("example_image.jpg")
    if location:
        print(f"  Location: {location['latitude']}, {location['longitude']}")

    return metadata


def example_7_policy_enforcement():
    """Example 7: Policy-based validation."""
    print("\nExample 7: Policy enforcement...")

    from src.verification.policy_engine import PolicyEngine, PolicyRule, PolicyRuleType, PolicyRuleSeverity
    from src.verification.policy_engine import OrganizationalPolicy

    # Create a custom policy
    policy = OrganizationalPolicy(
        name="social_media_content",
        description="Policy for social media content",
        version="1.0",
        rules=[
            PolicyRule(
                name="require_hash",
                description="Must have hash for integrity",
                rule_type=PolicyRuleType.REQUIRED_ASSERTION,
                severity=PolicyRuleSeverity.ERROR,
                assertion_label="c2pa.hash.data",
            ),
            PolicyRule(
                name="public_only",
                description="Social media must be public",
                rule_type=PolicyRuleType.CLASSIFICATION_CONSTRAINT,
                severity=PolicyRuleSeverity.ERROR,
                classification_levels=[ClassificationLevel.PUBLIC],
            ),
        ],
    )

    # Create policy engine and add policy
    policy_engine = PolicyEngine()
    policy_engine.add_policy(policy)

    # Create a manifest
    creator = ManifestCreator()
    manifest = creator.create(
        file_path="example_image.jpg",
        creator="social.media@example.com",
        title="Social Media Post",
        classification=ClassificationLevel.PUBLIC,
    )

    # Evaluate against policy
    result = policy_engine.evaluate(manifest, "social_media_content")

    print(f"✓ Policy evaluation complete")
    print(f"  Passed: {result.passed}")
    print(f"  Violations: {len(result.violations)}")

    for violation in result.violations:
        print(f"    - [{violation.severity}] {violation.message}")

    return result


def main():
    """Run all examples."""
    print("=" * 70)
    print("OpenMediaTrust - Basic Usage Examples")
    print("=" * 70)

    # Note: These examples assume example_image.jpg exists
    # For demonstration, we'll create a dummy file
    Path("example_image.jpg").touch()

    try:
        example_1_create_basic_manifest()
        example_2_sign_with_quantum_safe_crypto()
        example_3_enterprise_workflow()
        example_4_verify_manifest()
        example_5_custom_assertions()
        example_6_metadata_extraction()
        example_7_policy_enforcement()

        print("\n" + "=" * 70)
        print("All examples completed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        for file in ["example_image.jpg", "manifest_basic.json"]:
            if Path(file).exists():
                Path(file).unlink()


if __name__ == "__main__":
    main()
