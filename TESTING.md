# Testing Guide for Audio2Text

This guide covers how to write, run, and maintain tests for Audio2Text.

## Table of Contents

- [Overview](#overview)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Test Structure](#test-structure)
- [Coverage Requirements](#coverage-requirements)
- [CI/CD Pipeline](#cicd-pipeline)

---

## Overview

Audio2Text uses **pytest** as the testing framework with the following test types:

- **Unit Tests:** Test individual components in isolation (mocked dependencies)
- **Integration Tests:** Test component interactions and workflows
- **Coverage:** 70% minimum for backend, 80% for blocks

### Test Files

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_transcriber.py      # Transcriber class tests
├── test_config_manager.py   # ConfigManager tests
├── test_file_manager.py     # FileManager tests
├── test_hotkey_manager.py   # HotkeyManager tests
├── test_metadata.py         # TranscriptionMetadata tests
├── test_integration.py      # Integration tests
├── test_blocks.py           # Block system tests (existing)
└── data/                    # Test data directory
```

---

## Running Tests

### Run All Tests

```bash
# Basic test run
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=backend --cov=tests --cov-report=term-missing
```

### Run Specific Tests

```bash
# Run a specific test file
pytest tests/test_transcriber.py

# Run a specific test class
pytest tests/test_transcriber.py::TestTranscriberInitialization

# Run a specific test
pytest tests/test_transcriber.py::TestTranscriberInitialization::test_initialization

# Run tests by marker
pytest -m unit          # Only unit tests
pytest -m integration   # Only integration tests
pytest -m "not slow"    # Skip slow tests
```

### Run with Coverage Report

```bash
# Terminal report with missing lines
pytest --cov=backend --cov=tests --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov=backend --cov=tests --cov-report=html
open htmlcov/index.html  # macOS
start htmlcov/index.xml  # Windows

# XML report (for CI/CD)
pytest --cov=backend --cov=tests --cov-report=xml:coverage.xml
```

### Debugging Tests

```bash
# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

---

## Writing Tests

### Basic Test Structure

```python
"""
Tests for Transcriber class.
"""

import pytest
from unittest.mock import Mock, patch

# Import the class being tested
from backend.transcriber import Transcriber


@pytest.mark.unit  # Mark as unit test
class TestTranscriberInitialization:
    """Tests for Transcriber initialization."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for testing."""
        return {
            "config_manager": Mock(),
            "sound_manager": Mock(),
            # ... other dependencies
        }

    def test_initialization(self, mock_dependencies):
        """Test Transcriber initialization."""
        with patch('backend.transcriber.Groq'):
            transcriber = Transcriber(**mock_dependencies)

            assert transcriber.is_recording == False
            assert transcriber.hotkey == "F5"
```

### Using Fixtures

Fixtures are reusable test components defined in `conftest.py`:

```python
def test_with_fixture(mock_transcriber, mock_audio_file):
    """Test using fixtures from conftest.py."""
    result = mock_transcriber.transcribe(mock_audio_file)
    assert result["text"] is not None
```

### Mocking External Dependencies

Always mock external APIs and hardware:

```python
def test_with_mocked_api(mocker):
    """Test with mocked Groq API."""
    # Mock API response
    mock_response = {
        "text": "Texto de prueba",
        "language": "es"
    }

    # Patch the API call
    mocker.patch(
        'backend.transcriber.Groq.client.audio.transcriptions.create',
        return_value=mock_response
    )

    # Test the method
    result = transcriber.transcribe_with_groq("test.wav")
    assert result["text"] == "Texto de prueba"
```

### Testing Error Cases

Always test both success and failure paths:

```python
def test_invalid_api_key():
    """Test that invalid API key raises error."""
    with pytest.raises(ValueError):
        transcriber = Transcriber(api_key="")

def test_empty_transcription():
    """Test validation of empty transcription."""
    is_valid, error = transcriber.validate_text("")
    assert is_valid == False
    assert error is not None
```

---

## Test Structure

### Unit Tests

- **Purpose:** Test individual methods/classes in isolation
- **Dependencies:** Mock all external services (APIs, hardware, file system)
- **Speed:** Fast (< 1 second per test)
- **Location:** `tests/test_<module>.py`

Example:
```python
@pytest.mark.unit
class TestConfigManager:
    def test_get_config_value(self):
        config = ConfigManager()
        value = config.get("hotkey")
        assert value is not None
```

### Integration Tests

- **Purpose:** Test component interactions and workflows
- **Dependencies:** Use real components, mock only external APIs
- **Speed:** Slower (1-5 seconds per test)
- **Location:** `tests/test_integration.py`

Example:
```python
@pytest.mark.integration
class TestFullWorkflow:
    def test_record_to_transcribe(self):
        # Test: Config → Transcriber → Record → Transcribe
        config = ConfigManager()
        transcriber = Transcriber(config)
        transcriber.start_recording()
        # ... full workflow
```

---

## Coverage Requirements

### Minimum Coverage Targets

| Module | Target | Status |
|--------|--------|--------|
| Backend | 70% | Enforced in CI |
| Blocks | 80% | Enforced in CI |
| UI | 0% | Excluded |
| Tests | 0% | Excluded |

### Check Coverage

```bash
# Check current coverage
pytest --cov=backend --cov=tests --cov-report=term-missing

# Generate HTML report
pytest --cov=backend --cov=tests --cov-report=html
open htmlcov/index.html
```

### Exclude from Coverage

The following are excluded in `.coveragerc`:
- `tests/__pycache__` - Test cache files
- `__init__.py` - Package initialization
- `ui/` - UI modules (excluded from requirements)
- `ui_flet/` - Flet UI modules

---

## CI/CD Pipeline

### GitHub Actions Workflows

**CI Workflow** (`.github/workflows/ci.yml`):
1. **Lint:** flake8 + black (Ubuntu)
2. **Type Check:** mypy (Ubuntu)
3. **Test:** pytest + coverage (Windows, Python 3.8-3.11)
4. **Security:** Bandit scan (Ubuntu)

**Build Workflow** (`.github/workflows/build.yml`):
1. Triggers on git tags `v*.*.*`
2. Builds 3 variants: GENERAL, CONTRERAS, CUTIGNOLA
3. Creates GitHub Release with executables

### Local CI Simulation

To test locally what CI runs:

```bash
# 1. Lint
flake8 backend/ tests/
black --check backend/ tests/

# 2. Type check
mypy backend/ --ignore-missing-imports

# 3. Test with coverage
pytest --cov=backend --cov=tests --cov-report=xml --cov-report=term-missing

# 4. Security scan
pip install bandit
bandit -r backend/
```

---

## Best Practices

### DO ✅

- **Mock all external dependencies:** Groq API, sounddevice, keyboard
- **Use descriptive test names:** `test_transcribe_success_with_spanish_text`
- **Test both success and error cases**
- **Use fixtures for common test data**
- **Keep tests independent:** Each test should work in isolation
- **Aim for 70%+ coverage** on backend modules

### DON'T ❌

- **Don't call real APIs:** Always mock Groq, OpenAI, etc.
- **Don't access real hardware:** Mock sounddevice, keyboard
- **Don't write slow unit tests:** If it takes > 1 second, it's an integration test
- **Don't share state between tests:** Use fixtures, not class variables
- **Don't test UI components:** UI is excluded from coverage

---

## Common Patterns

### Testing File Operations

```python
def test_save_audio_file(tmp_path):
    """Test saving audio file using tmp_path fixture."""
    # Create test file in temp directory
    audio_file = tmp_path / "test.wav"

    # Save audio
    file_manager.save_audio_file(audio_data)

    # Verify file exists
    assert audio_file.exists()
```

### Testing with Mock Config

```python
@pytest.fixture
def mock_config():
    """Create mock configuration."""
    config = Mock()
    config.get.side_effect = lambda key, default=None: {
        "hotkey": "F5",
        "api_key": "test_key"
    }.get(key, default)
    return config
```

### Testing Async Operations

```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async function."""
    result = await async_function()
    assert result is not None
```

---

## Troubleshooting

### Tests Fail Locally but Pass in CI

- **Check Python version:** CI tests on 3.8-3.11, ensure you're using 3.8+
- **Check dependencies:** Run `pip install -r requirements.txt`
- **Check environment:** CI uses Windows, tests may be platform-specific

### Coverage Not Increasing

- **Run coverage with branch coverage:** `pytest --cov=backend --cov-branch`
- **Check what's not covered:** View `htmlcov/index.html`
- **Add tests for uncovered lines:** Focus on critical paths first

### Import Errors in Tests

```bash
# Add backend to path if needed
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# Or in Python:
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
```

---

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-mock Documentation](https://pytest-mock.readthedocs.io/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Python unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)

---

## Questions?

If you have questions about testing, please:

1. Check existing tests in `tests/` for examples
2. Consult this guide
3. Open an issue on GitHub

**Happy Testing! 🧪**
