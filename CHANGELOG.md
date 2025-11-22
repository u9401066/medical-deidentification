# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure with DDD architecture
- Core PHI identification using LLM (Ollama/OpenAI support)
- Batch processing for Excel files
- Token counting and performance statistics
- Support for 20+ PHI types (NAME, DATE, LOCATION, PHONE, etc.)
- Multi-language support (Traditional Chinese, English, Japanese, Korean, etc.)
- Customizable de-identification strategies
- RAG-based regulation context retrieval
- GPU acceleration support for Ollama
- Comprehensive documentation

### Fixed
- PHI detection response validation errors
- Automatic deduplication of identified entities
- Auto-calculation of total_entities count

## [0.1.0-beta] - 2025-11-22

### Initial Release
- First beta release
- Core de-identification functionality
- Batch processing support
- Basic documentation and examples

[Unreleased]: https://github.com/YOUR_USERNAME/medical-deidentification/compare/v0.1.0-beta...HEAD
[0.1.0-beta]: https://github.com/YOUR_USERNAME/medical-deidentification/releases/tag/v0.1.0-beta
