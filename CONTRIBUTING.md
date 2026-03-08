# Contributing to MCP Foundry

Thank you for considering a contribution to the MCP Foundry. Whether you're fixing a typo, adding a new exchange connector, or proposing a change to the UTI specification itself, your work helps build the foundation for agentic trading.

This guide will help you get started.

## Getting Started

### 1. Fork and clone

```bash
git clone https://github.com/YOUR_USERNAME/mcp-foundry.git
cd mcp-foundry
```

### 2. Set up your development environment

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev]"
```

### 3. Run the tests

```bash
pytest -v
```

If the tests pass, you're ready to start.

## How to Contribute

### Reporting Bugs

If you find a bug, please open a [GitHub Issue](https://github.com/mcp-foundry/mcp-foundry/issues) with:

- A clear title and description
- Steps to reproduce the issue
- Expected vs. actual behaviour
- Your Python version and OS

### Suggesting Features

We use [GitHub Discussions](https://github.com/mcp-foundry/mcp-foundry/discussions) for feature requests and design conversations. Before opening a new discussion, please check if someone has already proposed something similar.

### Submitting Code

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write your code** following the style guidelines below.

3. **Add tests** for any new functionality.

4. **Run the full test suite**:
   ```bash
   pytest -v
   ```

5. **Commit with a clear message**:
   ```bash
   git commit -m "Add Binance connector with spot and futures support"
   ```

6. **Push and open a pull request** against `main`.

### Adding a New Connector

New exchange connectors are the most impactful contribution you can make. Here's the process:

1. Read the [Connector Development Guide](docs/connector_development_guide.md).
2. Use `connectors/bybit.py` as your template.
3. Implement all methods from `core/interface.py`.
4. Register your connector in `connectors/__init__.py`.
5. Add tests in `tests/test_your_exchange.py`.
6. Update the README to list the new connector.

We'll review your PR carefully and work with you to get it merged.

## Style Guidelines

### Python

- **Python 3.11+** — use modern syntax (type hints, `match` statements where appropriate).
- **PEP 8** — follow standard Python style. We recommend using `ruff` for linting.
- **Type hints** — all public functions and methods should have complete type annotations.
- **Docstrings** — use reStructuredText format for docstrings. Every public class and method needs one.
- **Logging** — use the `logging` module, not `print()`. Follow the existing patterns.

### Commit Messages

- Use the imperative mood: "Add feature" not "Added feature"
- Keep the first line under 72 characters
- Reference issue numbers where applicable: "Fix #42: Handle empty order book response"

### Tests

- Use `pytest` with `pytest-asyncio` for async tests.
- Use the fixtures in `tests/conftest.py` — they provide mocked connectors and sample data.
- Aim for meaningful tests that verify behaviour, not just coverage numbers.

## Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

## Questions?

If you're unsure about anything, open a [GitHub Discussion](https://github.com/mcp-foundry/mcp-foundry/discussions) or reach out. We'd rather help you contribute than have you get stuck in silence.

---

Thank you for helping build the future of agentic trading infrastructure.
