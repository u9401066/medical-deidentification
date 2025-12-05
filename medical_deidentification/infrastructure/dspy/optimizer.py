"""
DSPy Optimizer for PHI Identification
DSPy PHI 識別優化器

Provides automatic prompt optimization using DSPy optimizers:
- BootstrapFewShot: Add few-shot examples automatically
- MIPRO: Multi-stage instruction optimization
- MIPROv2: Improved multi-stage optimization

提供使用 DSPy 優化器的自動 prompt 優化：
- BootstrapFewShot: 自動添加少量樣本示例
- MIPRO: 多階段指令優化
- MIPROv2: 改進的多階段優化

Key Optimization Goals:
1. Maximize F1 Score (balance precision/recall)
2. Minimize Detection Time (speed)
3. Minimize Prompt Length (efficiency)

主要優化目標：
1. 最大化 F1 分數（平衡精確率/召回率）
2. 最小化檢測時間（速度）
3. 最小化 Prompt 長度（效率）
"""

from typing import List, Optional, Tuple, Any
from dataclasses import dataclass
import json
import time
from pathlib import Path

try:
    import dspy
    from dspy.teleprompt import BootstrapFewShot, MIPROv2
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    dspy = None

from loguru import logger

from .phi_module import PHIIdentifier, PHIEntity, parse_phi_entities
from .metrics import PHIEvaluator, extract_phi_from_tags, EvaluationResult


@dataclass
class OptimizationResult:
    """
    Result of prompt optimization
    Prompt 優化結果
    """
    original_score: float
    optimized_score: float
    improvement: float
    
    # Performance comparison
    original_time_ms: float
    optimized_time_ms: float
    time_improvement: float
    
    # Prompt comparison
    original_prompt_length: int
    optimized_prompt_length: int
    prompt_reduction: float
    
    # Best configuration found
    best_module: Any  # Optimized DSPy module
    best_examples: List[Any]  # Few-shot examples used


class PHIPromptOptimizer:
    """
    Automatic PHI prompt optimizer using DSPy
    使用 DSPy 的自動 PHI prompt 優化器
    
    This optimizer uses DSPy's optimization algorithms to automatically:
    1. Find optimal few-shot examples
    2. Refine instruction prompts
    3. Balance accuracy vs efficiency
    
    這個優化器使用 DSPy 的優化算法自動：
    1. 找到最佳的少量樣本示例
    2. 優化指令 prompts
    3. 平衡準確性和效率
    
    Usage:
        # Prepare training data
        trainset = [
            dspy.Example(
                medical_text="Patient John Smith, age 45...",
                ground_truth=[("John Smith", "NAME"), ("45", "AGE")]
            ).with_inputs("medical_text")
            for ... 
        ]
        
        # Optimize
        optimizer = PHIPromptOptimizer()
        result = optimizer.optimize(trainset, max_iterations=10)
        
        # Use optimized module
        optimized_identifier = result.best_module
        entities = optimized_identifier(medical_text="...")
    """
    
    def __init__(
        self,
        evaluator: Optional[PHIEvaluator] = None,
        optimize_for_speed: bool = True,
        optimize_for_conciseness: bool = True,
        target_f1: float = 0.8,
        max_time_ms: float = 2000.0,
        max_prompt_length: int = 1000,
    ):
        """
        Initialize optimizer
        
        Args:
            evaluator: PHI evaluator instance (creates default if None)
            optimize_for_speed: Include time in optimization metric
            optimize_for_conciseness: Include prompt length in optimization metric
            target_f1: Target F1 score to achieve
            max_time_ms: Maximum acceptable detection time
            max_prompt_length: Maximum acceptable prompt length
        """
        if not DSPY_AVAILABLE:
            raise ImportError("DSPy not installed. Install with: pip install dspy-ai")
        
        self.evaluator = evaluator or PHIEvaluator(
            optimize_efficiency=optimize_for_speed or optimize_for_conciseness
        )
        self.optimize_for_speed = optimize_for_speed
        self.optimize_for_conciseness = optimize_for_conciseness
        self.target_f1 = target_f1
        self.max_time_ms = max_time_ms
        self.max_prompt_length = max_prompt_length
    
    def create_trainset_from_tagged_data(
        self,
        tagged_texts: List[str],
    ) -> List[Any]:
        """
        Create DSPy trainset from tagged text data
        從標記文本數據創建 DSPy 訓練集
        
        Args:
            tagged_texts: List of texts with PHI tags like 【PHI:TYPE:ID】content【/PHI】
            
        Returns:
            List of dspy.Example objects
        """
        trainset = []
        
        for text in tagged_texts:
            # Extract ground truth PHI from tags
            ground_truth = extract_phi_from_tags(text)
            
            # Remove tags to get clean text
            import re
            clean_text = re.sub(r'【PHI:\w+:[\w-]+】', '', text)
            clean_text = re.sub(r'【/PHI】', '', clean_text)
            
            # Create DSPy example
            example = dspy.Example(
                medical_text=clean_text.strip(),
                ground_truth=ground_truth,
            ).with_inputs("medical_text")
            
            trainset.append(example)
        
        logger.info(f"Created trainset with {len(trainset)} examples")
        return trainset
    
    def _metric_function(
        self,
        example: Any,
        prediction: Any,
        trace: Any = None,
    ) -> float:
        """
        Combined metric function for DSPy optimization
        用於 DSPy 優化的組合指標函數
        
        Combines:
        - F1 Score (accuracy) - 70% weight
        - Detection Time (speed) - 15% weight
        - Prompt Length (efficiency) - 15% weight
        """
        start_time = time.time()
        
        # Get ground truth
        ground_truth = example.ground_truth if hasattr(example, 'ground_truth') else []
        
        # Parse predicted entities
        if hasattr(prediction, 'phi_entities'):
            predicted = parse_phi_entities(
                prediction.phi_entities,
                example.medical_text
            )
        elif isinstance(prediction, list):
            predicted = prediction
        else:
            return 0.0
        
        # Calculate time
        detection_time_ms = (time.time() - start_time) * 1000
        
        # Calculate prompt length (estimate from trace if available)
        prompt_length = 0
        if trace:
            for step in trace:
                if hasattr(step, 'prompt'):
                    prompt_length += len(str(step.prompt))
        
        # Get evaluation result
        result = self.evaluator.evaluate(predicted, ground_truth)
        result.detection_time_ms = detection_time_ms
        result.prompt_length = prompt_length
        
        # Calculate final score
        f1_score = result.f1_score
        
        # Time penalty (if enabled)
        time_factor = 1.0
        if self.optimize_for_speed and detection_time_ms > 0:
            time_factor = min(1.0, self.max_time_ms / max(detection_time_ms, 1.0))
        
        # Prompt length penalty (if enabled)
        prompt_factor = 1.0
        if self.optimize_for_conciseness and prompt_length > 0:
            prompt_factor = min(1.0, self.max_prompt_length / max(prompt_length, 1.0))
        
        # Combined score: 70% F1 + 15% time + 15% prompt
        final_score = 0.7 * f1_score + 0.15 * time_factor + 0.15 * prompt_factor
        
        return final_score
    
    def optimize(
        self,
        trainset: List[Any],
        valset: Optional[List[Any]] = None,
        method: str = "bootstrap",
        max_bootstrapped_demos: int = 3,
        max_labeled_demos: int = 3,
        max_iterations: int = 10,
        save_path: Optional[str] = None,
    ) -> OptimizationResult:
        """
        Optimize PHI identifier using DSPy
        使用 DSPy 優化 PHI 識別器
        
        Args:
            trainset: Training examples (dspy.Example with medical_text and ground_truth)
            valset: Validation examples (optional, uses trainset subset if None)
            method: Optimization method ("bootstrap" or "mipro")
            max_bootstrapped_demos: Maximum bootstrapped few-shot examples
            max_labeled_demos: Maximum labeled few-shot examples
            max_iterations: Maximum optimization iterations
            save_path: Path to save optimized module
            
        Returns:
            OptimizationResult with comparison metrics
        """
        logger.info(f"Starting PHI prompt optimization with method: {method}")
        logger.info(f"Trainset size: {len(trainset)}")
        
        # Create base module
        base_module = PHIIdentifier()
        
        # Evaluate baseline
        logger.info("Evaluating baseline performance...")
        baseline_score, baseline_time = self._evaluate_module(base_module, trainset[:5])
        
        # Split valset if not provided
        if valset is None and len(trainset) > 5:
            valset = trainset[-3:]
            trainset = trainset[:-3]
        
        # Select optimizer
        if method == "bootstrap":
            optimizer = BootstrapFewShot(
                metric=self._metric_function,
                max_bootstrapped_demos=max_bootstrapped_demos,
                max_labeled_demos=max_labeled_demos,
            )
        elif method == "mipro":
            optimizer = MIPROv2(
                metric=self._metric_function,
                num_candidates=max_iterations,
                init_temperature=1.0,
            )
        else:
            raise ValueError(f"Unknown optimization method: {method}")
        
        # Run optimization
        logger.info(f"Running {method} optimization...")
        start_time = time.time()
        
        optimized_module = optimizer.compile(
            base_module,
            trainset=trainset,
        )
        
        optimization_time = time.time() - start_time
        logger.info(f"Optimization completed in {optimization_time:.1f}s")
        
        # Evaluate optimized module
        logger.info("Evaluating optimized performance...")
        optimized_score, optimized_time = self._evaluate_module(optimized_module, valset or trainset[:5])
        
        # Get prompt length comparison
        baseline_prompt_len = self._estimate_prompt_length(base_module)
        optimized_prompt_len = self._estimate_prompt_length(optimized_module)
        
        # Create result
        result = OptimizationResult(
            original_score=baseline_score,
            optimized_score=optimized_score,
            improvement=(optimized_score - baseline_score) / max(baseline_score, 0.01),
            original_time_ms=baseline_time,
            optimized_time_ms=optimized_time,
            time_improvement=(baseline_time - optimized_time) / max(baseline_time, 1.0),
            original_prompt_length=baseline_prompt_len,
            optimized_prompt_length=optimized_prompt_len,
            prompt_reduction=(baseline_prompt_len - optimized_prompt_len) / max(baseline_prompt_len, 1),
            best_module=optimized_module,
            best_examples=self._extract_examples(optimized_module),
        )
        
        # Save if requested
        if save_path:
            self._save_optimized_module(optimized_module, save_path)
            logger.info(f"Saved optimized module to {save_path}")
        
        # Print summary
        self._print_optimization_summary(result)
        
        return result
    
    def _evaluate_module(
        self,
        module: Any,
        examples: List[Any],
    ) -> Tuple[float, float]:
        """
        Evaluate a module on examples
        在樣本上評估模組
        
        Returns:
            (average_score, average_time_ms)
        """
        scores = []
        times = []
        
        for example in examples:
            start = time.time()
            try:
                prediction = module(medical_text=example.medical_text)
                elapsed_ms = (time.time() - start) * 1000
                
                score = self._metric_function(example, prediction)
                scores.append(score)
                times.append(elapsed_ms)
            except Exception as e:
                logger.warning(f"Evaluation failed for example: {e}")
                scores.append(0.0)
                times.append(0.0)
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        avg_time = sum(times) / len(times) if times else 0.0
        
        return avg_score, avg_time
    
    def _estimate_prompt_length(self, module: Any) -> int:
        """
        Estimate prompt length for a module
        估計模組的 prompt 長度
        """
        # Get the signature docstring as base prompt
        if hasattr(module, 'identify') and hasattr(module.identify, 'signature'):
            sig = module.identify.signature
            if hasattr(sig, '__doc__'):
                return len(sig.__doc__ or "")
        return 500  # Default estimate
    
    def _extract_examples(self, module: Any) -> List[Any]:
        """
        Extract few-shot examples from optimized module
        從優化模組中提取少量樣本示例
        """
        examples = []
        if hasattr(module, 'identify') and hasattr(module.identify, 'demos'):
            examples = module.identify.demos or []
        return examples
    
    def _save_optimized_module(self, module: Any, path: str) -> None:
        """
        Save optimized module to file
        將優化模組保存到文件
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save module state
        module.save(str(path))
    
    def _print_optimization_summary(self, result: OptimizationResult) -> None:
        """
        Print optimization summary
        打印優化摘要
        """
        print("\n" + "=" * 60)
        print("PHI Prompt Optimization Summary")
        print("=" * 60)
        
        print(f"\n📊 Accuracy:")
        print(f"  • Original Score:  {result.original_score:.2%}")
        print(f"  • Optimized Score: {result.optimized_score:.2%}")
        print(f"  • Improvement:     {result.improvement:+.2%}")
        
        print(f"\n⚡ Speed:")
        print(f"  • Original Time:  {result.original_time_ms:.1f} ms")
        print(f"  • Optimized Time: {result.optimized_time_ms:.1f} ms")
        print(f"  • Improvement:    {result.time_improvement:+.2%}")
        
        print(f"\n📝 Prompt Efficiency:")
        print(f"  • Original Length:  {result.original_prompt_length} chars")
        print(f"  • Optimized Length: {result.optimized_prompt_length} chars")
        print(f"  • Reduction:        {result.prompt_reduction:+.2%}")
        
        print(f"\n🎯 Few-shot Examples: {len(result.best_examples)}")
        
        print("\n" + "=" * 60)


def optimize_phi_identifier(
    tagged_texts: List[str],
    model_name: str = "qwen2.5:1.5b",
    method: str = "bootstrap",
    save_path: Optional[str] = None,
) -> OptimizationResult:
    """
    Convenience function to optimize PHI identifier
    優化 PHI 識別器的便捷函數
    
    Args:
        tagged_texts: List of texts with PHI tags
        model_name: Ollama model to use
        method: Optimization method
        save_path: Path to save optimized module
        
    Returns:
        OptimizationResult
    """
    from .phi_module import configure_dspy_ollama
    
    # Configure DSPy
    configure_dspy_ollama(model_name=model_name)
    
    # Create optimizer
    optimizer = PHIPromptOptimizer()
    
    # Create trainset
    trainset = optimizer.create_trainset_from_tagged_data(tagged_texts)
    
    # Optimize
    return optimizer.optimize(
        trainset=trainset,
        method=method,
        save_path=save_path,
    )
