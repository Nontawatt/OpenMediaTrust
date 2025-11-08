# Contributing to OpenMediaTrust

Thank you for your interest in contributing to OpenMediaTrust! This document provides guidelines for contributing to the project.

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please be respectful and professional in all interactions.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/yourusername/OpenMediaTrust/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs or screenshots

### Suggesting Features

1. Check existing issues and discussions
2. Create a new issue with:
   - Clear use case
   - Expected benefits
   - Possible implementation approach
   - Any alternatives considered

### Pull Requests

1. **Fork and Clone:**
   ```bash
   git clone https://github.com/yourusername/OpenMediaTrust.git
   cd OpenMediaTrust
   ```

2. **Create a Branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Setup Development Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

4. **Make Changes:**
   - Follow PEP 8 style guide
   - Add tests for new features
   - Update documentation as needed

5. **Run Tests:**
   ```bash
   pytest tests/
   pytest --cov=src tests/  # With coverage
   ```

6. **Run Code Quality Checks:**
   ```bash
   black src/ tests/
   isort src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

7. **Commit Changes:**
   ```bash
   git add .
   git commit -m "feat: add quantum-safe signature verification"
   ```

   Use conventional commit messages:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test changes
   - `refactor:` Code refactoring
   - `chore:` Build/tooling changes

8. **Push and Create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub

### PR Guidelines

- **Title:** Clear and descriptive
- **Description:** Explain what and why
- **Link Issues:** Reference related issues
- **Tests:** Include tests for new features
- **Documentation:** Update relevant docs
- **Single Responsibility:** One feature/fix per PR

## Development Guidelines

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings (Google style)
- Keep functions focused and small
- Maximum line length: 100 characters

**Example:**

```python
def create_manifest(
    file_path: str,
    creator: str,
    title: Optional[str] = None,
) -> Manifest:
    """
    Create a C2PA manifest for a file.

    Args:
        file_path: Path to the content file
        creator: Creator email or identifier
        title: Optional title for the content

    Returns:
        Created manifest object

    Raises:
        FileNotFoundError: If file does not exist
    """
    # Implementation
```

### Testing

- Write unit tests for new code
- Maintain >80% code coverage
- Use pytest fixtures for common setup
- Mock external dependencies
- Test edge cases and errors

**Example:**

```python
def test_create_manifest_success():
    """Test successful manifest creation."""
    creator = ManifestCreator()
    manifest = creator.create(
        file_path="test.jpg",
        creator="test@example.com",
        title="Test",
    )
    assert manifest.instance_id is not None
    assert manifest.title == "Test"

def test_create_manifest_file_not_found():
    """Test manifest creation with missing file."""
    creator = ManifestCreator()
    with pytest.raises(FileNotFoundError):
        creator.create(file_path="nonexistent.jpg", creator="test@example.com")
```

### Documentation

- Update README.md for significant changes
- Add docstrings to all public functions/classes
- Update API documentation for API changes
- Include examples in docs/

### Security

- Never commit secrets or keys
- Use environment variables for sensitive data
- Follow OWASP security guidelines
- Report security issues privately to security@openmediatrust.org

## Project Structure

```
OpenMediaTrust/
├── src/
│   ├── core/           # Core manifest functionality
│   ├── enterprise/     # Enterprise features
│   ├── verification/   # Verification layer
│   ├── storage/        # Storage backends
│   └── api/           # REST API
├── tests/             # Test suite
├── docs/              # Documentation
├── examples/          # Usage examples
├── scripts/           # Utility scripts
└── config/            # Configuration files
```

## Areas for Contribution

### High Priority

- [ ] Full ML-DSA/Dilithium implementation using liboqs
- [ ] SPHINCS+ signature scheme integration
- [ ] HSM integration for key storage
- [ ] Blockchain anchoring for manifests
- [ ] Advanced analytics dashboard
- [ ] Mobile SDK (iOS/Android)

### Medium Priority

- [ ] Additional storage backends (Azure, GCS)
- [ ] LDAP/AD integration improvements
- [ ] Webhook notification system
- [ ] GraphQL API
- [ ] CLI tool improvements

### Documentation

- [ ] Tutorial videos
- [ ] More usage examples
- [ ] Integration guides (DAM, CMS)
- [ ] Troubleshooting guide
- [ ] Performance tuning guide

## Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes
- Project documentation

## Questions?

- Open a [Discussion](https://github.com/yourusername/OpenMediaTrust/discussions)
- Join our community chat
- Email: developers@openmediatrust.org

Thank you for contributing to OpenMediaTrust!
