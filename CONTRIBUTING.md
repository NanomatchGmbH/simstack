# Contributing to SimStack

We welcome contributions to SimStack! This document provides guidelines for contributing to the GUI of the SimStack workflow platform.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [Pixi](https://pixi.sh/) package manager
- Git

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/NanomatchGmbH/simstack.git
   cd simstack
   ```

2. Set up the development environment:
   ```bash
   pixi shell  # Activates development environment with PySide6 and dev tools
   ```

3. Install pre-commit hooks:
   ```bash
   pixi run pre-commit-install
   ```

## Development Workflow

### Before Making Changes

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make sure all tests pass:
   ```bash
   pixi run tests
   ```

### Code Style and Quality

We maintain high code quality standards using automated tools:

- **Linting**: Run `pixi run lint` before committing
- **Pre-commit Hooks**: Automatically run on commit to enforce standards

### Testing

- Run all tests: `pixi run tests`
- Run with coverage: `pytest --cov=simstack tests/`
- Test specific functionality: `pytest tests/test_file.py::test_function_name`
- Single test file: `pixi run tests tests/path/to/test_file.py`

We aim for comprehensive test coverage. When adding new features:
- Write unit tests in the corresponding `tests/` directory
- Use `pytest-qt` for Qt widget testing with `qtbot` fixtures
- Mock complex dependencies appropriately

### Architecture Guidelines

SimStack follows an MVC-like architecture:

- **Application Layer**: Central controllers (`WFEditorApplication`, settings providers)
- **UI Layer**: Qt widgets organized in `view/` directory
- **Remote Operations**: SSH and cluster management components
- **WaNo System**: Workflow nodes with custom UI views. WaNos are not part of this repository.

When contributing:
- Follow existing patterns and code organization
- Place UI components in `view/` directory
- Use existing base classes and utilities from `lib/`
- Maintain separation between UI and business logic

### Code Conventions

- **Python Style**: Follow PEP 8, enforced by ruff
- **Type Hints**: Use type annotations (required by mypy)
- **Documentation**: Add docstrings for public methods and classes
- **Imports**: Organize imports logically, use absolute imports
- **Qt Patterns**: Follow Qt best practices for signal/slot connections and widget lifecycle

## Making a Pull Request

### Before Submitting

1. Ensure all tests pass:
   ```bash
   pixi run tests
   ```

2. Run linting and fix any issues:
   ```bash
   pixi run lint
   ```

3. Update tests if needed and ensure good coverage

### Pull Request Guidelines

- **Title**: Use descriptive titles that explain the change
- **Description**: Explain what changed, why, and how to test it
- **Size**: Keep PRs focused and reasonably sized
- **Tests**: Include tests for new functionality
- **Documentation**: Update relevant documentation

### PR Review Process

1. All PRs require review before merging
2. Address reviewer feedback promptly
3. Keep PRs up to date with main branch
4. Ensure CI checks pass

## Types of Contributions

### Bug Fixes

- Include reproduction steps in the issue/PR description
- Add regression tests when possible
- Reference the issue number in commit messages

### New Features

- Discuss significant features in an issue first
- Follow existing UI/UX patterns
- Ensure features work with the WaNo system
- Update relevant documentation

### Breaking Changes

- Discuss breaking changes in an issue before implementation
- Provide migration guide for users
- Update version appropriately
- Document all breaking changes in CHANGELOG.md

### Documentation Updates

- Keep documentation up to date with code changes
- Use clear, concise language
- Include code examples where helpful
- Update relevant sections when functionality changes

### Code Refactoring

- Maintain existing functionality while improving code structure
- Include comprehensive tests to ensure no regressions
- Document architectural improvements
- Keep refactoring PRs focused and well-scoped

### Performance Improvements

- Include benchmarks demonstrating performance gains
- Test across different environments and use cases
- Consider memory usage and startup time impacts
- Document performance characteristics

### UI/UX Improvements

- Maintain consistency with existing Qt design patterns
- Test on different screen sizes/resolutions
- Consider accessibility guidelines
- Provide screenshots in PR description

## Environment-Specific Development

### Available Environments

- `default`: Main development environment (PySide6, dev tools)
- `test`: Testing environment (pytest, pytest-qt, pytest-xvfb)
- `lint`: Linting environment (ruff, pre-commit)

Switch environments with: `pixi shell -e <environment-name>`

## Getting Help

- Check existing issues and discussions
- Review CLAUDE.md for development commands and architecture details
- Ask questions in pull request discussions

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help maintain a welcoming community
- Focus on technical merit in discussions

Thank you for contributing to SimStack!
