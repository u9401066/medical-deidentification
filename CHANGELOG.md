# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **MiniMind Ultra-Lightweight LLM Support** - 僅 26M-104M 參數的超輕量本地模型
  - `jingyaogong/minimind2` (104M, best performance)
  - `jingyaogong/minimind2-small` (26M, ultra-fast)
  - `jingyaogong/minimind2-r1` (R1-distilled reasoning)
- New LLM presets: `local_minimind()`, `local_minimind_small()`, `local_minimind_reasoning()`
- Comprehensive README with badges, quick start guide, and examples
- Detailed architecture documentation (DDD design patterns)
- Deployment guide with troubleshooting section
- Output directory structure: `data/output/results/`, `data/output/reports/`

### Changed
- Reorganized documentation structure under `docs/` folder
- Moved `OLLAMA_SETUP_GUIDE.md` to `docs/ollama-setup.md`
- Renamed `batch_processing.md` to `docs/batch-processing.md`
- Renamed `RAG_USAGE_GUIDE.md` to `docs/rag-usage.md`
- Updated output modules to infrastructure layer (DDD refactoring)

### Removed
- Outdated diagnostic reports (`ARCHITECTURE_FIX_STRATEGY_TYPE.md`, `CHAIN_DIAGNOSIS.md`)
- Old `STRUCTURE.md` (replaced by `docs/ARCHITECTURE.md`)

## [0.1.0-beta] - 2025-11-22

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

[Unreleased]: https://github.com/u9401066/medical-deidentification/compare/v0.1.0-beta...HEAD
[0.1.0-beta]: https://github.com/u9401066/medical-deidentification/releases/tag/v0.1.0-beta
