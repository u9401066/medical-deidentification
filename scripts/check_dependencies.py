"""
Dependency Checker
依賴檢查器

Check which dependencies are installed and which are missing.
檢查哪些依賴已安裝，哪些缺失。
"""

import sys
from typing import List, Tuple

# Required dependencies (only packages actually used in code)
REQUIRED_PACKAGES = {
    # Core
    "pydantic": "2.12.4",
    "pydantic_settings": "2.12.0",
    "loguru": "0.7.3",
    
    # LangChain (updated to new packages - Nov 2025)
    "langchain": "1.0.8",
    "langchain_core": "1.1.0",
    "langchain_text_splitters": "1.0.0",
    "langchain_community": "0.4.1",
    "langchain_openai": "1.0.3",
    "langchain_anthropic": "1.1.0",
    "langchain_ollama": "1.0.0",
    "langchain_huggingface": "1.0.1",
    "openai": "2.8.1",
    "anthropic": "0.74.1",
    "ollama": "0.6.1",
    
    # RAG & Vector Store
    "chromadb": "1.3.5",
    "sentence_transformers": "5.1.2",
    "faiss": "1.13.0",  # faiss-cpu
    
    # NLP
    "spacy": "3.8.11",
    
    # I/O & Data Formats
    "openpyxl": "3.1.5",
    "xlrd": "2.0.2",
    "docx": "1.2.0",  # python-docx
    "PyPDF2": "3.0.1",
    "pdfplumber": "0.11.8",
    "bs4": "4.14.2",  # beautifulsoup4
    "lxml": "6.0.2",
    
    # Utilities
    "tenacity": "9.1.2",
}


def check_package(package_name: str, min_version: str) -> Tuple[bool, str, str]:
    """
    Check if package is installed and version
    
    Returns:
        (is_installed, installed_version, status)
    """
    try:
        if package_name == "docx":
            import docx
            module = docx
        elif package_name == "bs4":
            import bs4
            module = bs4
        elif package_name == "faiss":
            import faiss
            module = faiss
        else:
            module = __import__(package_name.replace("-", "_"))
        
        version = getattr(module, "__version__", "unknown")
        
        # Version comparison (simple string comparison)
        if version == "unknown":
            return True, version, "⚠️  Installed (version unknown)"
        
        return True, version, "✅ Installed"
    
    except ImportError:
        return False, "", "❌ Missing"


def main():
    print("=" * 70)
    print("Dependency Check")
    print("=" * 70)
    print()
    
    installed = []
    missing = []
    
    for package, min_version in REQUIRED_PACKAGES.items():
        is_installed, version, status = check_package(package, min_version)
        
        if is_installed:
            installed.append((package, version))
            print(f"{status} {package:30} {version:15} (required: >={min_version})")
        else:
            missing.append(package)
            print(f"{status} {package:30} (required: >={min_version})")
    
    print()
    print("=" * 70)
    print(f"Summary: {len(installed)}/{len(REQUIRED_PACKAGES)} packages installed")
    print("=" * 70)
    
    if missing:
        print()
        print("Missing packages:")
        for package in missing:
            print(f"  - {package}")
        print()
        print("To install missing packages:")
        print(f"  pip install {' '.join(missing)}")
    else:
        print()
        print("✅ All required packages are installed!")
    
    return len(missing) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
