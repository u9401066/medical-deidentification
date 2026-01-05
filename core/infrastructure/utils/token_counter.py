"""
Token Counter Utility | Token 計數工具

Utility for counting tokens in text for performance analysis.
用於計算文本中的 token 數量以進行性能分析。
"""

from typing import Optional
from loguru import logger


class TokenCounter:
    """
    Token counter for text analysis
    文本分析的 Token 計數器
    
    Uses approximate character-based estimation for local models.
    對於本地模型使用基於字符的近似估算。
    
    For more accurate counting, install tiktoken:
    更準確的計數需要安裝 tiktoken：
        pip install tiktoken
    """
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        """
        Initialize token counter
        
        Args:
            model_name: Model name for encoding (e.g., 'llama3.1:8b', 'gpt-4')
        """
        self.model_name = model_name
        self._encoder = None
        
        # Try to import tiktoken for accurate counting
        try:
            import tiktoken
            self._tiktoken = tiktoken
            if "gpt" in model_name.lower():
                try:
                    self._encoder = tiktoken.encoding_for_model(model_name)
                    logger.debug(f"Using tiktoken encoder for {model_name}")
                except KeyError:
                    # Fallback to cl100k_base for unknown GPT models
                    self._encoder = tiktoken.get_encoding("cl100k_base")
                    logger.debug(f"Using cl100k_base encoder for {model_name}")
        except ImportError:
            logger.debug("tiktoken not installed, using approximate counting")
            self._tiktoken = None
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text
        計算文本中的 token 數量
        
        Args:
            text: Input text
        
        Returns:
            Approximate token count
        """
        if not text:
            return 0
        
        if self._encoder:
            # Use tiktoken for accurate counting
            return len(self._encoder.encode(text))
        else:
            # Approximate counting for local models
            # Based on empirical observation:
            # - English: ~4 chars per token
            # - Chinese: ~1.5-2 chars per token
            # - Mixed: ~3 chars per token (conservative estimate)
            return self._approximate_count(text)
    
    def _approximate_count(self, text: str) -> int:
        """
        Approximate token count using character-based heuristics
        使用基於字符的啟發式方法近似計算 token 數
        
        Args:
            text: Input text
        
        Returns:
            Approximate token count
        """
        # Count characters by type
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        other_chars = len(text) - chinese_chars - english_chars
        
        # Estimate tokens based on character type
        # Chinese: ~1.5 chars per token
        # English: ~4 chars per token
        # Other (punctuation, numbers, spaces): ~2 chars per token
        estimated_tokens = (
            chinese_chars / 1.5 +
            english_chars / 4.0 +
            other_chars / 2.0
        )
        
        return int(estimated_tokens)
    
    def format_token_rate(
        self,
        total_tokens: int,
        elapsed_seconds: float
    ) -> str:
        """
        Format token processing rate
        格式化 token 處理速率
        
        Args:
            total_tokens: Total tokens processed
            elapsed_seconds: Elapsed time in seconds
        
        Returns:
            Formatted string (e.g., "150 tokens/sec")
        """
        if elapsed_seconds <= 0:
            return "N/A"
        
        tokens_per_sec = total_tokens / elapsed_seconds
        return f"{tokens_per_sec:.1f} tokens/sec"
    
    def get_statistics(
        self,
        input_text: str,
        output_text: str,
        elapsed_seconds: float
    ) -> dict:
        """
        Get comprehensive token statistics
        獲取完整的 token 統計信息
        
        Args:
            input_text: Input prompt text
            output_text: Output response text
            elapsed_seconds: Processing time
        
        Returns:
            Dictionary with token statistics
        """
        input_tokens = self.count_tokens(input_text)
        output_tokens = self.count_tokens(output_text)
        total_tokens = input_tokens + output_tokens
        
        stats = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "elapsed_seconds": elapsed_seconds,
            "tokens_per_second": total_tokens / elapsed_seconds if elapsed_seconds > 0 else 0,
            "input_tokens_per_second": input_tokens / elapsed_seconds if elapsed_seconds > 0 else 0,
            "output_tokens_per_second": output_tokens / elapsed_seconds if elapsed_seconds > 0 else 0,
        }
        
        return stats
    
    def print_statistics(
        self,
        input_text: str,
        output_text: str,
        elapsed_seconds: float
    ):
        """
        Print token statistics to console
        將 token 統計信息打印到控制台
        
        Args:
            input_text: Input prompt text
            output_text: Output response text
            elapsed_seconds: Processing time
        """
        stats = self.get_statistics(input_text, output_text, elapsed_seconds)
        
        print(f"\n{'='*60}")
        print("Token Statistics | Token 統計")
        print(f"{'='*60}")
        print(f"Input tokens:           {stats['input_tokens']:>10,}")
        print(f"Output tokens:          {stats['output_tokens']:>10,}")
        print(f"Total tokens:           {stats['total_tokens']:>10,}")
        print(f"Elapsed time:           {stats['elapsed_seconds']:>10.2f}s")
        print(f"{'─'*60}")
        print(f"Throughput:             {stats['tokens_per_second']:>10.1f} tokens/sec")
        print(f"Input rate:             {stats['input_tokens_per_second']:>10.1f} tokens/sec")
        print(f"Output rate:            {stats['output_tokens_per_second']:>10.1f} tokens/sec")
        print(f"{'='*60}\n")


# Global default counter
_default_counter: Optional[TokenCounter] = None


def get_default_counter(model_name: str = "llama3.1:8b") -> TokenCounter:
    """
    Get or create default token counter
    獲取或創建默認的 token 計數器
    
    Args:
        model_name: Model name for encoding
    
    Returns:
        TokenCounter instance
    """
    global _default_counter
    if _default_counter is None:
        _default_counter = TokenCounter(model_name)
    return _default_counter


def count_tokens(text: str, model_name: str = "llama3.1:8b") -> int:
    """
    Quick function to count tokens in text
    快速計算文本中的 token 數量
    
    Args:
        text: Input text
        model_name: Model name for encoding
    
    Returns:
        Token count
    
    Examples:
        >>> count_tokens("Hello, world!")
        4
        >>> count_tokens("醫療去識別化系統")
        6
    """
    counter = get_default_counter(model_name)
    return counter.count_tokens(text)
