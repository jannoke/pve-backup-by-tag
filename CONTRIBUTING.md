# Contributing to pve-backup-by-tag

Thank you for your interest in contributing to this project! This document provides guidelines for contributing.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. Check if the issue already exists in the GitHub issue tracker
2. If not, create a new issue with:
   - Clear, descriptive title
   - Detailed description of the issue or feature
   - Steps to reproduce (for bugs)
   - Expected vs. actual behavior
   - Your environment (Python version, Proxmox version, etc.)

### Submitting Changes

1. Fork the repository
2. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes following the coding standards below
4. Test your changes thoroughly
5. Commit your changes with clear, descriptive commit messages
6. Push to your fork
7. Submit a pull request

## Coding Standards

### Python Style
- Follow PEP 8 style guide
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and single-purpose
- Maximum line length: 100 characters

### Code Organization
- Keep related functionality together
- Separate concerns (API, filtering, backup execution, etc.)
- Use type hints where appropriate
- Handle errors gracefully with specific exceptions

### Documentation
- Update README.md if adding new features
- Update example configuration if adding new options
- Add comments for complex logic
- Include usage examples

## Testing

Before submitting a pull request:

1. Run the basic tests:
   ```bash
   python3 test_basic.py
   ```

2. Test the script manually with:
   - Help output: `python3 pve-backup-by-tag.py --help`
   - Syntax check: `python3 -m py_compile pve-backup-by-tag.py`

3. If possible, test with a Proxmox instance (or at least in dry-run mode)

## Adding New Features

When adding new features, ensure:

1. The feature is aligned with the project goals
2. It doesn't break existing functionality
3. It includes appropriate error handling
4. It's documented in README.md
5. Configuration options are added to config.example.yaml
6. Command-line options follow existing patterns

## Areas for Contribution

### High Priority
- Integration tests with mock Proxmox API
- Better progress tracking for long-running backups
- Parallel backup support in distributed mode
- Email notifications for backup status
- Backup rotation/retention policies

### Medium Priority
- Web UI for configuration and monitoring
- Backup verification functionality
- Incremental backup support
- Better performance metrics and statistics
- Support for backup hooks/scripts

### Documentation
- More usage examples
- Troubleshooting guide expansion
- Video tutorials or screenshots
- Translation to other languages

## Code Review Process

All submissions require review. We'll:

1. Check code quality and style
2. Verify functionality
3. Test for edge cases
4. Ensure documentation is updated
5. Run security scans

## Questions?

If you have questions about contributing, feel free to:
- Open an issue for discussion
- Comment on existing issues
- Reach out to the maintainers

Thank you for contributing!
