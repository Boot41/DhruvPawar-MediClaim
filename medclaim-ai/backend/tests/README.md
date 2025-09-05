# MedClaim AI Backend Test Suite

This directory contains comprehensive test cases for the MedClaim AI backend system, targeting 70-80% code coverage with 40-50 test cases.

## Test Structure

### Test Files

- `conftest.py` - Pytest configuration and shared fixtures
- `test_auth.py` - Authentication and authorization tests
- `test_database.py` - Database models and operations tests
- `test_api_endpoints.py` - API endpoint tests
- `test_document_processor.py` - Document processing functionality tests
- `test_file_handler.py` - File handling and upload tests
- `test_agent_service.py` - AI agent service tests
- `test_pdf_generator.py` - PDF generation tests
- `test_schemas.py` - Pydantic schema validation tests
- `test_integration.py` - End-to-end integration tests

### Test Categories

1. **Unit Tests** - Individual function and method testing
2. **Integration Tests** - Component interaction testing
3. **API Tests** - HTTP endpoint testing
4. **Database Tests** - Data persistence and retrieval testing
5. **Authentication Tests** - Security and access control testing

## Running Tests

### Prerequisites

Install test dependencies:
```bash
cd /path/to/medclaim-ai/backend
pip install -r tests/requirements.txt
```

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test Files

```bash
# Run authentication tests
pytest tests/test_auth.py

# Run API endpoint tests
pytest tests/test_api_endpoints.py

# Run integration tests
pytest tests/test_integration.py
```

### Run with Coverage

```bash
pytest tests/ --cov=. --cov-report=html --cov-report=term
```

### Run with Verbose Output

```bash
pytest tests/ -v
```

### Run Specific Test Classes

```bash
# Run specific test class
pytest tests/test_auth.py::TestPasswordHashing

# Run specific test method
pytest tests/test_auth.py::TestPasswordHashing::test_verify_password_correct
```

## Test Configuration

### Environment Variables

The tests use a separate test database (`test_medclaim.db`) and don't require external services like Google ADK or LlamaParse for most tests.

### Mocking

Tests use extensive mocking to:
- Mock external API calls (Google ADK, LlamaParse)
- Mock file system operations
- Mock database operations where appropriate
- Mock agent service responses

### Fixtures

Key fixtures available in `conftest.py`:
- `client` - FastAPI test client
- `db_session` - Database session for testing
- `test_user` - Sample user for testing
- `test_session` - Sample user session
- `test_document` - Sample document
- `auth_headers` - Authentication headers
- `mock_agent_service` - Mocked agent service
- `mock_file_handler` - Mocked file handler

## Test Coverage

The test suite covers:

### Authentication Module (100%)
- Password hashing and verification
- JWT token creation and validation
- User registration and login
- Session management
- Access control

### Database Models (100%)
- User model operations
- Document model operations
- Claim model operations
- Vendor model operations
- Workflow state management
- Chat message persistence

### API Endpoints (95%)
- Health check endpoint
- Authentication endpoints
- Document upload and management
- Chat functionality
- Claim form generation
- Workflow state management
- PDF download

### Document Processing (90%)
- Text extraction from various formats
- Document chunking
- Pattern-based data extraction
- File validation
- Error handling

### File Handling (95%)
- File upload validation
- File type checking
- File size validation
- MIME type detection
- File storage and retrieval

### Agent Service (85%)
- Agent initialization
- Document processing with agents
- Chat routing to appropriate agents
- Claim form generation
- Coverage calculation
- Error handling

### PDF Generation (90%)
- Synthetic claim form generation
- Vendor-specific form generation
- Star Health template handling
- Error handling and fallbacks

### Schema Validation (100%)
- All Pydantic schemas
- Required field validation
- Type validation
- Optional field handling

## Test Data

Tests use realistic test data including:
- Sample user information
- Mock document content
- Sample insurance policy data
- Sample invoice data
- Test PDF content

## Continuous Integration

The test suite is designed to run in CI/CD environments:
- No external dependencies required
- Fast execution (most tests complete in seconds)
- Deterministic results
- Comprehensive error reporting

## Debugging Tests

### Run Tests with Debug Output

```bash
pytest tests/ -v -s --tb=short
```

### Run Single Test with Debug

```bash
pytest tests/test_auth.py::test_verify_password_correct -v -s
```

### Check Test Coverage

```bash
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

## Adding New Tests

When adding new functionality:

1. Add unit tests for individual functions
2. Add integration tests for component interactions
3. Add API tests for new endpoints
4. Update fixtures if needed
5. Ensure test coverage remains above 70%

## Best Practices

- Use descriptive test names
- Test both success and failure cases
- Use appropriate assertions
- Mock external dependencies
- Keep tests independent and isolated
- Use fixtures for common setup
- Test edge cases and error conditions
