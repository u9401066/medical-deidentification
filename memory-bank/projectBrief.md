# Project Brief

## Title | 專案名稱

Medical Text De-identification Toolkit | 醫療文本去識別化工具套件

## Purpose | 專案目的

Develop an open-source Python package for automated de-identification of medical records using LLM/Agent technology. The toolkit provides:
- 透過 LLM/Agent 技術自動化處理醫療病歷去識別化
- Support for batch processing of large-scale medical texts
- 支援少量測試與大量批次處理
- Customizable de-identification strategies and rules
- 可自定義去識別化標準與規則
- Open to GitHub for community contribution

## Goals | 專案目標

1. **Core Functionality | 核心功能**
   - Automated identification and removal/masking of PHI (Protected Health Information)
   - 自動識別並移除/遮罩個人健康資訊

2. **Flexibility | 靈活性**
   - Customizable de-identification rules and strategies
   - 可自定義去識別化規則與策略
   - Support multiple LLM providers (OpenAI, Anthropic, local models)
   - 支援多種 LLM 提供者

3. **Scalability | 可擴展性**
   - Efficient batch processing for large datasets
   - 大量資料批次處理效能
   - Handle both small test sets and production-scale data
   - 同時支援小型測試與生產級資料量

4. **Open Source | 開源**
   - MIT/Apache 2.0 License
   - Comprehensive documentation
   - Community-driven development

## Target Users | 目標用戶

- **Medical Researchers | 醫學研究人員**: Processing clinical data for research
- **Healthcare IT Teams | 醫療資訊團隊**: De-identifying EHR data for compliance
- **Data Scientists | 資料科學家**: Preparing medical datasets for ML training
- **Regulatory Teams | 法規遵循團隊**: Ensuring HIPAA/GDPR compliance

## Constraints | 限制條件

- Must comply with HIPAA, GDPR, and other privacy regulations
- 必須符合醫療隱私法規
- Follow MVP development principle - prioritize core features
- 遵循 MVP 原則 - 優先核心功能
- Maintain high accuracy in PHI detection (minimize false negatives)
- 保持高準確度,降低漏檢率
- Performance: Process at least 1000 records/hour
- 效能要求:至少每小時處理 1000 筆

## Stakeholders | 利害關係人

- Medical institutions requiring data de-identification
- Open-source community contributors
- Healthcare compliance officers
- Research ethics committees
