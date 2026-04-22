# Contributing to Claudio

Thank you for your interest in contributing to Claudio AI DJ!

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/YOUR_USERNAME/claudio-music-agent/issues)
2. If not, create a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version)

### Suggesting Features

1. Open a new issue with the `enhancement` label
2. Describe the feature and its use case
3. Explain why it would be useful

### Pull Requests

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Commit with clear messages
7. Push to your fork
8. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/claudio-music-agent.git
cd claudio-music-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your test credentials

# Run CLI
./cli.py
```

## Code Style

- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small

## Testing

```bash
# Run tests
python -m pytest

# Run with coverage
python -m pytest --cov=.
```

## Questions?

Feel free to open an issue for any questions!
