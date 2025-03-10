# Academic Organizer Tests

This directory contains tests for the Academic Organizer application.

## Test Structure

- `unit/`: Unit tests for individual components
- `integration/`: Integration tests for component interactions
- `system/`: System tests for end-to-end functionality
- `performance/`: Performance tests for critical operations

## Running Tests

To run all tests:

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/unit/test_config.py
```

To run tests with coverage report:

```bash
pytest --cov=academic_organizer
```

## Writing Tests

When writing tests, follow these guidelines:

1. Each test should focus on a single functionality
2. Use descriptive test names that explain what is being tested
3. Follow the Arrange-Act-Assert pattern
4. Use fixtures for common setup
5. Mock external dependencies

Example test:

```python
def test_load_config_default_values():
    """Test that default configuration values are loaded correctly."""
    config = load_config()
    assert config["application"]["name"] == "Academic Organizer"
    assert config["database"]["type"] == "sqlite"
```

## Test Coverage Goals

- Unit tests: 90% coverage
- Integration tests: 80% coverage
- System tests: Key user workflows
- Performance tests: Critical operations