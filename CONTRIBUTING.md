# Contributing to Medical De-identification Toolkit

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/medical-deidentification.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest`
6. Commit your changes: `git commit -m "Add your feature"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

## 📋 Development Guidelines

### Code Style

- Follow PEP 8 style guide
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Keep functions small and focused (single responsibility)

### Architecture

This project follows Domain-Driven Design (DDD) principles:

- **Domain Layer**: Core business logic (entities, value objects)
- **Application Layer**: Use cases and orchestration
- **Infrastructure Layer**: External integrations (LLM, RAG, etc.)
- **Interface Layer**: APIs and user interfaces

### Commit Messages

Follow conventional commits format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions or changes
- `chore:` Maintenance tasks

Example: `feat: Add support for custom PHI types`

### Testing

- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage
- Include integration tests for critical paths

### Documentation

- Update README.md if adding new features
- Add docstrings to all public APIs
- Update CHANGELOG.md with your changes
- Provide examples for new functionality

## 🐛 Reporting Issues

When reporting issues, please include:

1. Clear description of the problem
2. Steps to reproduce
3. Expected vs actual behavior
4. Environment details (Python version, OS, etc.)
5. Relevant logs or error messages

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check if the feature already exists or is planned
2. Describe the use case clearly
3. Explain why this feature would be valuable
4. Provide examples if possible

## 🔒 Security

If you discover a security vulnerability:

1. **DO NOT** create a public issue
2. Contact the maintainers directly
3. Provide detailed information about the vulnerability
4. Wait for confirmation before disclosing publicly

## 📝 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive criticism
- Assume good intentions

## 🙏 Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes
- Project documentation

Thank you for contributing to making healthcare data privacy better! 🎉
