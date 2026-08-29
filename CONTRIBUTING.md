# Contributing

Thank you for your interest in contributing to the Enterprise AI Platform.

This repository is primarily a learning and portfolio reference project for LLMOps, AI platform engineering, GPU inference and observability.

## Development workflow

1. Fork the repository.
2. Create a feature branch.
3. Make the change.
4. Add or update tests.
5. Run the test suite.
6. Run the repository checks.
7. Open a pull request.

## Validation

Run:

```bash
PYTHONPATH=services/runtime-api python -m pytest -q
