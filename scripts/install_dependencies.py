"""
Install Dependencies Script
依賴安裝腳本

Install all required packages in batches to avoid conflicts.
分批安裝所有必需的套件以避免衝突。
"""

import subprocess
import sys
from pathlib import Path

# Python executable
PYTHON_EXE = "D:/workspace251122/.venv/Scripts/python.exe"

# Package groups (install in order)
PACKAGE_GROUPS = [
    {
        "name": "Core Dependencies",
        "packages": [
            "pydantic>=2.6.0",
            "pydantic-settings>=2.1.0",
            "loguru>=0.7.2",
            "python-dotenv>=1.0.0",
            "tenacity>=8.2.3",
        ]
    },
    {
        "name": "LangChain Core",
        "packages": [
            "langchain>=0.1.0",
            "langchain-community>=0.0.10",
        ]
    },
    {
        "name": "LLM Providers",
        "packages": [
            "langchain-openai>=0.0.5",
            "openai>=1.12.0",
            "langchain-anthropic>=0.1.0",
            "anthropic>=0.18.0",
        ]
    },
    {
        "name": "RAG & Vector Store",
        "packages": [
            "sentence-transformers>=2.3.1",
            "faiss-cpu>=1.7.4",
            "chromadb>=0.4.22",
        ]
    },
    {
        "name": "Document Processing",
        "packages": [
            "xlrd>=2.0.1",
            "python-docx>=1.1.0",
            "PyPDF2>=3.0.1",
            "pdfplumber>=0.10.3",
            "beautifulsoup4>=4.12.3",
            "lxml>=5.1.0",
        ]
    },
    {
        "name": "NLP (Optional)",
        "packages": [
            "spacy>=3.7.2",
        ]
    },
]


def install_package_group(group_name: str, packages: list) -> bool:
    """
    Install a group of packages
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"Installing: {group_name}")
    print(f"{'='*70}\n")
    
    for package in packages:
        print(f"  Installing {package}...")
    
    try:
        cmd = [PYTHON_EXE, "-m", "pip", "install"] + packages
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(result.stdout)
        print(f"\n✅ {group_name} installed successfully!\n")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error installing {group_name}:")
        print(e.stderr)
        print(f"\nYou can try installing manually:")
        print(f"  {PYTHON_EXE} -m pip install {' '.join(packages)}\n")
        return False


def main():
    print("=" * 70)
    print("Medical De-identification Toolkit")
    print("Dependency Installation")
    print("=" * 70)
    print()
    print(f"Python: {PYTHON_EXE}")
    print(f"Working Directory: {Path.cwd()}")
    print()
    
    # Upgrade pip first
    print("Upgrading pip...")
    try:
        subprocess.run(
            [PYTHON_EXE, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            check=True
        )
        print("✅ pip upgraded\n")
    except subprocess.CalledProcessError:
        print("⚠️  Failed to upgrade pip, continuing anyway...\n")
    
    # Install each group
    success_count = 0
    failed_groups = []
    
    for group in PACKAGE_GROUPS:
        success = install_package_group(group["name"], group["packages"])
        if success:
            success_count += 1
        else:
            failed_groups.append(group["name"])
    
    # Summary
    print("\n" + "=" * 70)
    print("Installation Summary")
    print("=" * 70)
    print(f"\nSuccessful: {success_count}/{len(PACKAGE_GROUPS)} groups")
    
    if failed_groups:
        print(f"\nFailed groups:")
        for group_name in failed_groups:
            print(f"  - {group_name}")
        print("\n⚠️  Some packages failed to install.")
        print("Please check the error messages above and install manually if needed.")
    else:
        print("\n✅ All packages installed successfully!")
    
    print("\nNext steps:")
    print("  1. Run: python scripts/check_dependencies.py")
    print("  2. Run: python examples/structured_output_demo.py")
    print()
    
    return len(failed_groups) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
