"""
分析未使用的套件
Analyze unused packages
"""

import subprocess
import sys
from pathlib import Path

# 實際代碼中使用的套件
USED_PACKAGES = {
    # 核心套件
    "langchain", "langchain-core", "langchain-community", "langchain-text-splitters",
    "langchain-anthropic", "langchain-openai", "langchain-ollama", "langchain-huggingface",
    
    # LLM 提供商
    "anthropic", "openai", "ollama",
    
    # RAG & Embeddings
    "faiss-cpu", "sentence-transformers", "transformers", "tokenizers", "huggingface-hub",
    
    # 深度學習
    "torch", "numpy",
    
    # 資料處理
    "pydantic", "pydantic-settings", "pydantic-core",
    "pandas", "openpyxl",  # Excel 處理
    
    # 日誌與工具
    "loguru", "rich", "tqdm",
    "tenacity", "backoff",
    
    # 配置
    "python-dotenv", "pyyaml",
    
    # HTTP/網路（LangChain 依賴）
    "httpx", "httpcore", "requests",
    
    # 其他關鍵依賴
    "typing-extensions", "typing-inspection",
    "jsonpatch", "jsonpointer",
}

# pyproject.toml 中明確聲明但可能未使用的套件
DECLARED_PACKAGES = {
    "chromadb",  # 我們用 FAISS，不用 ChromaDB
    "spacy",  # NLP，未在代碼中看到
    "typer",  # CLI，測試中未使用
    "xlrd",  # 舊版 Excel，pandas 可能會用
}

# 開發依賴（不需要在生產環境）
DEV_PACKAGES = {
    "pytest", "pytest-cov", "pytest-asyncio", "pytest-mock",
    "black", "isort", "mypy", "pylint", "ruff",
    "mkdocs", "mkdocs-material", "mkdocstrings",
    "ipython", "jupyter", "ipykernel",
    "poetry", "poetry-core",
}

# Poetry 相關
POETRY_PACKAGES = {
    "poetry", "poetry-core", "cleo", "crashtest", "dulwich",
    "findpython", "installer", "keyring", "pbs-installer",
    "pkginfo", "pyproject-hooks", "shellingham", "tomlkit",
    "trove-classifiers", "virtualenv",
}

# Kubernetes 相關（可能不需要）
K8S_PACKAGES = {
    "kubernetes", "websocket-client", "google-auth", "oauthlib",
    "requests-oauthlib", "pyasn1", "pyasn1-modules", "rsa",
}

# LangGraph 相關（如果不用 agent）
LANGGRAPH_PACKAGES = {
    "langgraph", "langgraph-checkpoint", "langgraph-prebuilt", "langgraph-sdk",
}

# FastAPI/Web 相關（如果只是命令列工具）
WEB_PACKAGES = {
    "fastapi", "starlette", "uvicorn", "watchfiles", "httptools",
    "websockets", "python-multipart",
}

# Chroma 相關
CHROMA_PACKAGES = {
    "chromadb", "chroma-hnswlib", "onnxruntime", "posthog",
    "pulsar-client", "pypika", "bcrypt",
}

# 其他可能不需要的
MAYBE_UNUSED = {
    "xlrd",  # 舊版 Excel 讀取，pandas 可能用 openpyxl
    "beautifulsoup4", "lxml", "soupsieve",  # HTML 解析
    "pypdf2", "pdfplumber", "pdfminer.six", "pypdfium2",  # PDF（如果不處理 PDF）
    "python-docx",  # Word 文件
    "spacy", "spacy-legacy", "spacy-loggers",  # NLP
    "typer", "typer-slim", "click",  # CLI
}

def get_installed_packages():
    """取得已安裝套件列表"""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=freeze"],
        capture_output=True, text=True
    )
    packages = set()
    for line in result.stdout.strip().split('\n'):
        if '==' in line:
            pkg = line.split('==')[0].strip().lower()
            packages.add(pkg)
    return packages

def main():
    print("🔍 分析未使用的套件...")
    print()
    
    installed = get_installed_packages()
    
    # 分析
    potentially_unused = []
    
    # 1. Kubernetes
    k8s_installed = [p for p in K8S_PACKAGES if p.lower() in installed]
    if k8s_installed:
        potentially_unused.append(("❌ Kubernetes 相關 (可能不需要)", k8s_installed))
    
    # 2. LangGraph
    langgraph_installed = [p for p in LANGGRAPH_PACKAGES if p.lower() in installed]
    if langgraph_installed:
        potentially_unused.append(("⚠️ LangGraph (如果不用 agent)", langgraph_installed))
    
    # 3. ChromaDB
    chroma_installed = [p for p in CHROMA_PACKAGES if p.lower() in installed]
    if chroma_installed:
        potentially_unused.append(("❌ ChromaDB 相關 (我們用 FAISS)", chroma_installed))
    
    # 4. FastAPI/Web
    web_installed = [p for p in WEB_PACKAGES if p.lower() in installed]
    if web_installed:
        potentially_unused.append(("⚠️ Web/FastAPI (如果只是命令列)", web_installed))
    
    # 5. Poetry
    poetry_installed = [p for p in POETRY_PACKAGES if p.lower() in installed]
    if poetry_installed:
        potentially_unused.append(("ℹ️ Poetry 開發工具 (執行時不需要)", poetry_installed))
    
    # 6. 其他可能未使用
    maybe_installed = [p for p in MAYBE_UNUSED if p.lower() in installed]
    if maybe_installed:
        potentially_unused.append(("⚠️ 其他可能未使用", maybe_installed))
    
    # 輸出
    total_unused = 0
    for category, packages in potentially_unused:
        print(f"\n{category}:")
        for pkg in sorted(packages):
            print(f"  - {pkg}")
            total_unused += 1
    
    print(f"\n\n📊 總計: {total_unused} 個套件可能不需要")
    
    # 建議移除的命令
    print("\n" + "="*80)
    print("建議執行:")
    print("="*80)
    
    all_to_remove = []
    for _, packages in potentially_unused:
        all_to_remove.extend(packages)
    
    if all_to_remove:
        # 分批輸出
        print("\n# 1. ChromaDB 相關 (確定不需要)")
        chroma_to_remove = [p for p in chroma_installed]
        if chroma_to_remove:
            print(f"pip uninstall -y {' '.join(chroma_to_remove)}")
        
        print("\n# 2. Kubernetes 相關 (確定不需要)")
        k8s_to_remove = [p for p in k8s_installed]
        if k8s_to_remove:
            print(f"pip uninstall -y {' '.join(k8s_to_remove)}")
        
        print("\n# 3. LangGraph (如果確定不用)")
        if langgraph_installed:
            print(f"pip uninstall -y {' '.join(langgraph_installed)}")
        
        print("\n# 4. FastAPI/Web (如果只是命令列工具)")
        if web_installed:
            print(f"pip uninstall -y {' '.join(web_installed)}")

if __name__ == "__main__":
    main()
