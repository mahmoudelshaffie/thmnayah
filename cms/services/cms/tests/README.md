# Category Management Integration Tests

This directory contains comprehensive integration tests for the CMS category management API endpoints, specifically focusing on the GET /categories and POST /categories endpoints.

## Test Structure

```
tests/
├── integration/
│   └── test_categories_api.py     # Main integration tests
├── conftest.py                    # Test fixtures and configuration
├── utils.py                       # Test utilities and helpers  
├── run_tests.py                   # Test runner script
└── README.md                      # This documentation
```

## Test Coverage

### GET /categories Endpoint Tests

The integration tests cover the following scenarios for listing categories:

#### Basic Functionality
- ✅ List categories with empty database
- ✅ List categories with existing data
- ✅ Pagination with various page sizes and offsets
- ✅ Response structure validation

#### Filtering Options
- ✅ Filter by category type (TOPIC, FORMAT, AUDIENCE, etc.)
- ✅ Filter by parent category ID
- ✅ Filter by active/inactive status
- ✅ Search by category name (English and Arabic)
- ✅ Language preference handling

#### Error Handling
- ✅ Invalid pagination parameters
- ✅ Invalid category type filters
- ✅ Invalid query parameters

#### Performance
- ✅ Response time validation with large datasets
- ✅ Efficient pagination with 100+ categories

### POST /categories Endpoint Tests

The integration tests cover the following scenarios for creating categories:

#### Basic Category Creation
- ✅ Create category with minimal required data
- ✅ Create category with complete data (all optional fields)
- ✅ Hierarchical category creation with parent relationships
- ✅ Response structure validation

#### Multilingual Support
- ✅ Multiple language name/description validation
- ✅ Language code validation
- ✅ Text length limits and validation

#### Field Validation
- ✅ Required field validation (name, category_type)
- ✅ Color scheme format validation (hex colors)
- ✅ Sort order validation (non-negative integers)
- ✅ SEO keywords limits (max 20 items)
- ✅ Text field length limits (max 1000 characters)

#### Business Logic
- ✅ Automatic path generation for hierarchical structure
- ✅ Duplicate slug prevention
- ✅ Parent category validation
- ✅ Category type validation

#### Security & Authentication
- ✅ Authentication requirement validation
- ✅ Authorization header validation

#### Error Scenarios
- ✅ Missing required fields
- ✅ Invalid multilingual data
- ✅ Invalid enum values
- ✅ Nonexistent parent category
- ✅ Constraint violations

## Test Features

### Comprehensive Test Utilities

The test suite includes robust utilities for:

- **Category Creation**: `create_test_category()` with customizable parameters
- **Data Validation**: `assert_category_response_structure()` for response validation
- **Multilingual Testing**: `assert_multilingual_field()` for language validation
- **Pagination Testing**: `assert_pagination_structure()` for pagination validation
- **Hierarchy Testing**: `create_category_hierarchy()` for complex structures
- **Authentication**: `get_auth_headers()` for mock authentication

### Test Data Builder

Fluent interface for creating test data:

```python
category_data = (CategoryTestDataBuilder()
    .with_name({"en": "Technology", "ar": "التكنولوجيا"})
    .with_type("TOPIC")
    .with_seo(
        title={"en": "Tech Courses", "ar": "دورات التكنولوجيا"},
        description={"en": "Learn technology", "ar": "تعلم التكنولوجيا"},
        keywords=["tech", "programming"]
    )
    .with_styling("/icons/tech.svg", "/banners/tech.jpg", "#2ECC71")
    .build())
```

### Fixtures and Test Data

Comprehensive fixtures for different testing scenarios:

- `sample_category_data`: Complete category with all fields
- `minimal_category_data`: Required fields only
- `multilingual_test_data`: Various language combinations
- `invalid_test_data`: Invalid data for negative testing
- `performance_test_config`: Performance testing parameters

## Running the Tests

### Prerequisites

Ensure you have the required dependencies installed:

```bash
pip install pytest pytest-asyncio httpx sqlalchemy pydantic fastapi
```

### Quick Start

Run the category API integration tests:

```bash
# Using the test runner script
python tests/run_tests.py --category-api

# Or directly with pytest
python -m pytest tests/integration/test_categories_api.py -v
```

### Test Runner Options

The `run_tests.py` script provides various testing options:

```bash
# Check test environment setup
python tests/run_tests.py --check

# Run integration tests
python tests/run_tests.py --integration

# Run all tests with coverage
python tests/run_tests.py --all

# Run only fast tests (exclude slow/performance tests)
python tests/run_tests.py --fast

# Run performance tests
python tests/run_tests.py --performance

# Run with debug output
python tests/run_tests.py --debug

# Clean test artifacts
python tests/run_tests.py --clean
```

### Direct Pytest Commands

For more control, run pytest directly:

```bash
# Run specific test class
python -m pytest tests/integration/test_categories_api.py::TestGetCategoriesAPI -v

# Run specific test method
python -m pytest tests/integration/test_categories_api.py::TestCreateCategoryAPI::test_create_category_minimal_data -v

# Run with markers
python -m pytest -m "integration and not slow" -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# Run with debug output
python -m pytest tests/integration/test_categories_api.py -v -s --log-cli-level=DEBUG
```

## Test Configuration

### Pytest Configuration

The tests use `pytest.ini` for configuration:

- **Test Discovery**: Automatically finds test files and functions
- **Markers**: Categorizes tests (integration, unit, slow, performance, etc.)
- **Coverage**: Configured for app source code with exclusions
- **Timeout**: 60-second timeout to prevent hanging tests
- **Logging**: Console and file logging for debugging

### Environment Setup

Tests use a separate SQLite database (`test.db`) that is:

- Created fresh for each test function
- Automatically cleaned up after tests
- Isolated from development/production databases

### Async Test Support

Tests use `pytest-asyncio` for testing async FastAPI endpoints:

```python
async def test_list_categories_empty_database(self, async_client: AsyncClient, db: Session):
    response = await async_client.get("/api/v1/categories/")
    assert response.status_code == 200
```

## Test Markers

Tests are categorized with markers for selective execution:

- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.unit`: Unit tests  
- `@pytest.mark.slow`: Tests taking >1 second
- `@pytest.mark.performance`: Performance/load tests
- `@pytest.mark.multilingual`: Multilingual functionality tests
- `@pytest.mark.validation`: Input validation tests
- `@pytest.mark.hierarchy`: Hierarchical category tests

## Continuous Integration

### GitHub Actions Example

```yaml
name: Category API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio httpx
    - name: Run category API tests
      run: python tests/run_tests.py --category-api
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      if: success()
```

### Local Development

Add to your pre-commit hooks:

```bash
# Run fast tests before commit
python tests/run_tests.py --fast

# Run full test suite before push
python tests/run_tests.py --all
```

## Test Results and Coverage

### Coverage Reports

Tests generate coverage reports in multiple formats:

- **Terminal**: Real-time coverage during test execution
- **HTML**: Detailed report in `htmlcov/index.html`
- **XML**: Machine-readable format for CI systems

### Expected Coverage

The integration tests provide coverage for:

- API endpoint handlers (categories.py)
- Request/response models (categories.py models)
- Database operations through ORM
- Error handling and validation
- Authentication and authorization flows

Target coverage: **>80%** for category management endpoints

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Database Errors**: Check SQLite permissions and cleanup
3. **Async Errors**: Verify pytest-asyncio configuration
4. **Authentication Errors**: Check mock auth setup in conftest.py

### Debug Mode

Run tests with maximum verbosity and debug logging:

```bash
python tests/run_tests.py --debug
```

### Test Environment Check

Verify environment setup:

```bash
python tests/run_tests.py --check
```

## Contributing

### Adding New Tests

1. Follow the existing test structure and naming conventions
2. Use appropriate test markers
3. Include both positive and negative test cases
4. Add comprehensive docstrings
5. Use the test utilities and fixtures provided

### Test Data

- Use the `CategoryTestDataBuilder` for complex test data
- Add new fixtures to `conftest.py` for reusable data
- Include multilingual test cases where applicable
- Test edge cases and boundary conditions

### Documentation

- Update this README when adding new test scenarios
- Document any new utilities or fixtures
- Include examples for complex test setups

## Related Documentation

- [API Documentation](../docs/api/categories.md)
- [Category Model Documentation](../docs/models/category.md)
- [Database Schema](../docs/database/schema.md)
- [Development Setup](../README.md)