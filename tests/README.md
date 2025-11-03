# Test Suite for FASER Alignment Scripts

This directory contains tests for validating the HTCondor DAGman-based alignment workflow.

## Test Files

### Unit Tests

- **`test_config.py`**: Tests for configuration management
  - Configuration file loading and validation
  - Path configuration
  - Error handling for invalid configurations

- **`test_dag_generation.py`**: Tests for DAG generation
  - DAG file creation
  - Submit file generation
  - Job dependency management
  - Directory structure creation

### Integration Tests

- **`test_integration.sh`**: End-to-end integration test
  - Full workflow validation
  - Configuration management
  - DAG generation (dry run)
  - Submit file validation
  - Directory structure verification

## Running Tests

### Run All Tests

```bash
# Run all unit tests
python3 tests/test_config.py -v
python3 tests/test_dag_generation.py -v

# Run integration test
bash tests/test_integration.sh
```

### Run Specific Test

```bash
# Run specific test class
python3 tests/test_config.py TestAlignmentConfig -v

# Run specific test method
python3 tests/test_config.py TestAlignmentConfig.test_load_config -v
```

## Test Coverage

The test suite covers:

1. **Configuration Management**
   - JSON configuration loading
   - Path validation
   - Default configuration creation
   - Error handling

2. **DAG Generation**
   - DAG file structure
   - Job definitions
   - Dependency chains
   - Submit file content
   - HTCondor settings

3. **Integration**
   - Complete workflow execution (dry run)
   - File generation
   - Directory structure
   - RawList processing

## Test Requirements

- Python 3.6+
- Standard library modules (no external dependencies)
- Bash shell (for integration tests)

## Adding New Tests

When adding new functionality:

1. Add unit tests to the appropriate test file
2. Update integration test if workflow changes
3. Ensure tests are independent and can run in any order
4. Use temporary directories for file operations
5. Clean up test artifacts in tearDown/cleanup

## Continuous Integration

These tests are designed to run in CI/CD pipelines without requiring:
- HTCondor installation
- CERN infrastructure access
- External dependencies

They validate the correctness of generated files and workflow logic.
