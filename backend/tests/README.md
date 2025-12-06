# Knowledge Base API - Automated Testing Guide

## 🧪 Running the Tests

### Quick Start
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
cd backend
pytest tests/test_kb_automated.py -v

# Run with coverage
pytest tests/test_kb_automated.py --cov=app --cov-report=html

# Run specific test class
pytest tests/test_kb_automated.py::TestCogneeService -v

# Run specific test
pytest tests/test_kb_automated.py::TestCogneeService::test_upload_and_index_success -v
```

## 📋 Test Suite Overview

### Test Classes

#### 1. **TestCogneeService** (5 tests)
Tests the Cognee service layer:
- ✅ Upload and index success
- ✅ Upload with non-existent file
- ✅ Get processing status
- ✅ Query unindexed dataset
- ✅ Delete dataset

#### 2. **TestKnowledgeBaseAPI** (7 tests)
Tests API endpoints:
- ✅ Upload invalid file type
- ✅ Upload success
- ✅ List KB files
- ✅ Get status (not found)
- ✅ Query not indexed document
- ✅ Delete success
- ✅ Delete not found

#### 3. **TestEndToEndWorkflow** (1 test)
Complete workflow:
- ✅ Upload → Status → List → Delete

**Total: 13 comprehensive tests**

## 🎯 Test Features

### Fixtures
- `test_db_engine` - In-memory test database
- `db_session` - Database session per test
- `test_user` - Mock user
- `test_llm_config` - Mock LLM configuration
- `test_file` - Temporary test document
- `auth_headers` - Mock authentication

### Coverage
- ✅ Happy path scenarios
- ✅ Error handling
- ✅ Edge cases
- ✅ Validation
- ✅ Cleanup

## 📊 Expected Output

```
================================ test session starts =================================
collected 13 items

tests/test_kb_automated.py::TestCogneeService::test_upload_and_index_success PASSED
tests/test_kb_automated.py::TestCogneeService::test_upload_nonexistent_file PASSED
tests/test_kb_automated.py::TestCogneeService::test_get_processing_status PASSED
tests/test_kb_automated.py::TestCogneeService::test_query_unindexed_dataset PASSED
tests/test_kb_automated.py::TestCogneeService::test_delete_dataset PASSED
tests/test_kb_automated.py::TestKnowledgeBaseAPI::test_upload_kb_file_invalid_type PASSED
tests/test_kb_automated.py::TestKnowledgeBaseAPI::test_upload_kb_file_success PASSED
tests/test_kb_automated.py::TestKnowledgeBaseAPI::test_get_kb_files PASSED
tests/test_kb_automated.py::TestKnowledgeBaseAPI::test_get_kb_status_not_found PASSED
tests/test_kb_automated.py::TestKnowledgeBaseAPI::test_query_kb_not_indexed PASSED
tests/test_kb_automated.py::TestKnowledgeBaseAPI::test_delete_kb_success PASSED
tests/test_kb_automated.py::TestKnowledgeBaseAPI::test_delete_kb_not_found PASSED
tests/test_kb_automated.py::TestEndToEndWorkflow::test_full_workflow PASSED

================================ 13 passed in 2.34s ==================================
```

## 🔧 CI/CD Integration

### GitHub Actions
```yaml
name: KB API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio httpx
      - run: pytest tests/test_kb_automated.py -v
```

## 🐛 Debugging Failed Tests

### Verbose Output
```bash
pytest tests/test_kb_automated.py -vv -s
```

### Run Single Test
```bash
pytest tests/test_kb_automated.py::TestCogneeService::test_upload_and_index_success -vv -s
```

### Print Debug Info
```bash
pytest tests/test_kb_automated.py --log-cli-level=DEBUG
```

## ✅ Test Checklist

Before deploying:
- [ ] All 13 tests pass
- [ ] No warnings
- [ ] Coverage > 80%
- [ ] Integration tests pass
- [ ] End-to-end workflow works

## 🚀 Continuous Testing

Set up pre-commit hooks:
```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/test_kb_automated.py --tb=short
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

Now tests run automatically before every commit! 🎉
