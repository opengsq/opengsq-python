# Contributing to `opengsq-python`

Thank you for your interest in contributing to OpenGSQ Python. This guide will help you get started with the contribution process.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](/CODE_OF_CONDUCT.md) By participating, you are expected to uphold this code.

## Project Structure

The `opengsq-python` is organized as follows:

- `/docs` - Documentation
- `/opengsq` - Core opengsq library
- `/tests` - Tests

## Development Guidelines

When contributing to `opengsq-python`:

- Keep changes focused. Large PRs are harder to review and unlikely to be accepted. We recommend opening an issue and discussing it with us first.
- Write clear, self-explanatory code. Use comments only when truly necessary.
- Follow the existing code style and conventions.

## Getting Started

1. Fork the repository to your GitHub account
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/opengsq-python.git
   cd opengsq-python
   ```
3. Create a Virtual Python Environment
   ```bash
   python -m venv venv
   ```
4. Activate the Environment
   #### Windows
   ```bash
   venv\Scripts\activate.bat
   ```
   #### Linux, Mac
   ```bash
   source venv/bin/activate
   ```
6. Install Python dependencies
   ```bash
   pip install -r requirements.txt
   ```
7. Install Python dependencies (tests)
   ```bash
   pip install -r tests/requirements.txt
   ```
8. Install Python dependencies (docs)
   ```bash
   pip install -r docs/requirements.txt
   ```

## Code Formatting with Ruff

We use [Ruff](https://github.com/astral-sh/ruff) for code formatting and linting. Before committing, please ensure your code is properly formatted:

```bash
# Format all code
ruff format

# Check for linting issues
ruff check
```

## Documentation (`/docs`)

1. Sphinx API Documentation Generation
```bash
sphinx-apidoc -o docs/api opengsq
```

2. Sphinx HTML Documentation Build
```bash
sphinx-build -b html docs docs/_build
```

- Keep documentation up-to-date with code changes
- Use clear, concise language
- Include code examples for common use cases
- Document any breaking changes in the migration guide
- Follow the existing documentation style and structure
