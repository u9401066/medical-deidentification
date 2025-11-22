# Medical Text De-identification Toolkit | 醫療文本去識別化工具套件

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Overview | 專案概述

An open-source Python toolkit for automated de-identification of medical records using LLM/Agent technology.

基於 LLM/Agent 技術的開源 Python 醫療病歷自動去識別化工具套件。

### Key Features | 主要特色

- 🤖 **LLM-Powered**: Leverages state-of-the-art language models for accurate PHI detection
- ⚡ **Batch Processing**: Efficiently process large volumes of medical texts
- 🎯 **Customizable**: Define your own de-identification rules and strategies
- 🌍 **Multi-language**: Support for 10+ languages including Traditional Chinese, English, Japanese, Korean, and more
- 🔧 **Extensible PHI Types**: 20+ standard PHI types plus custom type definitions
  - Standard types: Name, Date, Location, Medical Record Number, etc.
  - Extended types: Hospital Name, Ward Number, Age >90, Rare Diseases, etc.
  - Custom types: Define institution-specific identifiers
- 🎚️ **Strictness Levels**: Choose between standard and strict de-identification modes
- 🔒 **Privacy-First**: HIPAA and GDPR compliant design
- 🐍 **Pure Python**: Easy integration with existing Python workflows
- 📦 **Open Source**: MIT licensed, community-driven development

## Installation | 安裝

```bash
pip install medical-deidentification
```

Or install from source:

```bash
git clone https://github.com/YOUR_USERNAME/medical-deidentification.git
cd medical-deidentification
poetry install
```

> **Note**: Replace `YOUR_USERNAME` with your GitHub username

## Quick Start | 快速開始

```python
from medical_deidentification import DeidentificationPipeline
from medical_deidentification.strategies import RedactionStrategy

# Initialize pipeline
pipeline = DeidentificationPipeline(
    llm_provider="openai",
    strategy=RedactionStrategy()
)

# De-identify a single document
text = "Patient John Doe, DOB: 1980-05-15, visited on 2024-01-10..."
result = pipeline.process(text)

print(result.deidentified_text)
print(result.detected_entities)
```

## Project Status | 專案狀態

🚧 **Beta Version** - Active Development

**Version**: 0.1.0-beta  
**Status**: Research & Development (Not Production Ready)

This project follows MVP (Minimum Viable Product) principles and DDD (Domain-Driven Design) architecture.

本專案遵循 MVP 最小可行產品原則與 DDD 領域驅動設計架構。

### Performance Benchmarks | 效能基準

Current performance using Ollama llama3.1:8b (GPU mode):
- **Processing Speed**: ~27 seconds per document
- **Throughput**: ~3-4 documents per minute
- **PHI Detection**: Average 95% confidence
- **Supported Document Length**: Up to 2000 characters (auto-chunking for longer texts)

Note: Performance varies based on:
- Document complexity
- LLM provider (Ollama vs OpenAI)
- Hardware specifications (GPU/CPU)
- PHI density in text

## Documentation | 文件

- [Architecture Design](./memory-bank/architect.md)
- [Product Context](./memory-bank/productContext.md)
- [Project Brief](./memory-bank/projectBrief.md)
- [Development Guidelines](./memory-bank/systemPatterns.md)

## Development | 開發

### Prerequisites | 前置需求

- Python 3.11 or higher
- Poetry for dependency management
- Git for version control

### Setup Development Environment | 設置開發環境

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/medical-deidentification.git
cd medical-deidentification

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run tests
pytest
```

### Development Principles | 開發原則

This project follows strict development guidelines:

1. **Language**: 繁體中文 (Traditional Chinese) + Academic English
2. **Documentation**: Update Memory Bank (MEM) for all documentation changes
3. **Version Control**: GIT + MEM synchronization for all changes
4. **Methodology**: MVP (Minimum Viable Product) development
5. **Architecture**: DDD (Domain-Driven Design)

## Contributing | 貢獻

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

歡迎貢獻！請參閱貢獻指南。

## License | 授權

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Privacy & Compliance | 隱私與合規

⚠️ **Important**: Never commit real Protected Health Information (PHI) to this repository.

重要提醒：絕不將真實個人健康資訊提交到此儲存庫。

This toolkit is designed to help with HIPAA and GDPR compliance but users are responsible for ensuring proper usage in their specific context.

## Contact | 聯絡

- GitHub Issues: [Report bugs or request features](https://github.com/yourusername/medical-deidentification/issues)
- Discussions: [Join the community](https://github.com/yourusername/medical-deidentification/discussions)

## Acknowledgments | 致謝

Built with ❤️ using modern Python tooling and LLM technology.

---

**Note**: This project is under active development. APIs may change before v1.0.0 release.
