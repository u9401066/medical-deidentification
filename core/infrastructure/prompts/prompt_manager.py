"""
Prompt Manager - YAML Prompt Configuration Loader
Prompt 管理器 - YAML Prompt 配置載入器

Manages YAML-based prompt configurations with:
- Loading and validation
- Version control
- Template rendering (Jinja2)
- Model-specific configurations
- Optimization result saving

管理 YAML 格式的 prompt 配置，包括：
- 載入與驗證
- 版本控制
- 模板渲染 (Jinja2)
- 模型特定配置
- 優化結果保存
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from jinja2 import BaseLoader, Environment, TemplateSyntaxError
from loguru import logger

# Default prompts directory
DEFAULT_PROMPTS_DIR = Path(__file__).parent / "prompts"


@dataclass
class PHITypeConfig:
    """PHI type configuration from YAML"""
    name: str
    description: str
    examples: list[str] = field(default_factory=list)
    regex_patterns: list[str] = field(default_factory=list)
    priority: str = "medium"
    special_rule: str | None = None


@dataclass
class FewShotExample:
    """Few-shot example for optimization"""
    input: str
    output: str
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "input": self.input,
            "output": self.output,
            "note": self.note,
        }


@dataclass
class PromptTemplate:
    """Single prompt template"""
    name: str
    template: str
    variables: list[str] = field(default_factory=list)

    def render(self, **kwargs) -> str:
        """Render template with variables"""
        env = Environment(loader=BaseLoader())
        try:
            tmpl = env.from_string(self.template)
            return tmpl.render(**kwargs)
        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error in {self.name}: {e}")
            # Fallback: simple string formatting
            result = self.template
            for key, value in kwargs.items():
                result = result.replace(f"{{{{ {key} }}}}", str(value))
            return result


@dataclass
class ModelConfig:
    """Model-specific configuration"""
    model_name: str
    prompt_style: str = "simplified"
    temperature: float = 0.1
    max_tokens: int = 1024
    use_cot: bool = False
    notes: str = ""


@dataclass
class OptimizationConfig:
    """Optimization settings"""
    default_method: str = "bootstrap_fewshot"
    bootstrap_fewshot: dict[str, Any] = field(default_factory=lambda: {
        "max_bootstrapped_demos": 3,
        "max_labeled_demos": 3,
        "max_rounds": 1,
    })
    mipro: dict[str, Any] = field(default_factory=lambda: {
        "num_candidates": 10,
        "init_temperature": 1.0,
    })
    targets: dict[str, float] = field(default_factory=lambda: {
        "min_f1_score": 0.80,
        "max_response_time_ms": 5000,
        "max_prompt_tokens": 1500,
    })
    weights: dict[str, float] = field(default_factory=lambda: {
        "f1_score": 0.70,
        "time_factor": 0.15,
        "prompt_factor": 0.15,
    })


@dataclass
class PromptConfig:
    """
    Complete prompt configuration loaded from YAML
    從 YAML 載入的完整 prompt 配置
    """
    # Metadata
    name: str
    version: str
    description: str
    author: str = ""
    created_at: str | None = None
    updated_at: str | None = None

    # Benchmark results
    benchmark: dict[str, Any] = field(default_factory=dict)

    # PHI types
    phi_types: dict[str, PHITypeConfig] = field(default_factory=dict)

    # Prompt templates
    prompts: dict[str, PromptTemplate] = field(default_factory=dict)

    # Few-shot examples
    few_shot_examples: list[FewShotExample] = field(default_factory=list)

    # Optimization settings
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)

    # Model-specific configs
    model_configs: dict[str, ModelConfig] = field(default_factory=dict)

    # Source file path
    source_path: Path | None = None

    def get_prompt(
        self,
        name: str = "simplified",
        model_name: str | None = None,
        **kwargs
    ) -> str:
        """
        Get rendered prompt for a specific model
        取得特定模型的渲染後 prompt
        
        Args:
            name: Prompt template name (default: "simplified")
            model_name: Model name for model-specific config
            **kwargs: Variables to pass to template
            
        Returns:
            Rendered prompt string
        """
        # Get model-specific prompt style if model specified
        if model_name and model_name in self.model_configs:
            config = self.model_configs[model_name]
            name = config.prompt_style

        # Get template
        if name not in self.prompts:
            available = list(self.prompts.keys())
            raise ValueError(f"Prompt '{name}' not found. Available: {available}")

        template = self.prompts[name]

        # Add phi_types to kwargs if needed
        if "phi_types" in template.variables and "phi_types" not in kwargs:
            kwargs["phi_types"] = {
                k: {"description": v.description, "examples": v.examples}
                for k, v in self.phi_types.items()
            }

        return template.render(**kwargs)

    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get configuration for a specific model"""
        if model_name in self.model_configs:
            return self.model_configs[model_name]

        # Return default config
        return ModelConfig(
            model_name=model_name,
            prompt_style="simplified",
            temperature=0.1,
            max_tokens=1024,
        )

    def get_phi_type_list(self) -> list[str]:
        """Get list of all PHI type names"""
        return list(self.phi_types.keys())

    def get_few_shot_examples(self, n: int | None = None) -> list[FewShotExample]:
        """Get few-shot examples (optionally limited)"""
        if n is None:
            return self.few_shot_examples
        return self.few_shot_examples[:n]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (for saving)"""
        return {
            "metadata": {
                "name": self.name,
                "version": self.version,
                "description": self.description,
                "author": self.author,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "benchmark": self.benchmark,
            },
            "phi_types": {
                k: {
                    "description": v.description,
                    "examples": v.examples,
                    "regex_patterns": v.regex_patterns,
                    "priority": v.priority,
                }
                for k, v in self.phi_types.items()
            },
            "prompts": {
                k: {
                    "template": v.template,
                    "variables": v.variables,
                }
                for k, v in self.prompts.items()
            },
            "few_shot_examples": [e.to_dict() for e in self.few_shot_examples],
            "optimization": {
                "dspy": {
                    "default_method": self.optimization.default_method,
                    "bootstrap_fewshot": self.optimization.bootstrap_fewshot,
                    "mipro": self.optimization.mipro,
                },
                "targets": self.optimization.targets,
                "weights": self.optimization.weights,
            },
            "model_configs": {
                k: {
                    "prompt_style": v.prompt_style,
                    "temperature": v.temperature,
                    "max_tokens": v.max_tokens,
                    "use_cot": v.use_cot,
                    "notes": v.notes,
                }
                for k, v in self.model_configs.items()
            },
        }


class PromptManager:
    """
    Prompt configuration manager
    Prompt 配置管理器
    
    Handles loading, validation, and management of YAML prompt configurations.
    
    Usage:
        # Load default prompt
        manager = PromptManager()
        config = manager.load("phi_identification")
        
        # Get prompt for specific model
        prompt = config.get_prompt(model_name="granite4:1b", medical_text="...")
        
        # Save optimized version
        manager.save_optimized(config, new_version="1.1.0")
    """

    def __init__(self, prompts_dir: str | Path | None = None):
        """
        Initialize prompt manager
        
        Args:
            prompts_dir: Directory containing prompt YAML files
        """
        self.prompts_dir = Path(prompts_dir) if prompts_dir else DEFAULT_PROMPTS_DIR
        self._cache: dict[str, PromptConfig] = {}

        logger.info(f"PromptManager initialized with dir: {self.prompts_dir}")

    def load(
        self,
        name: str,
        version: str | None = None,
        reload: bool = False,
    ) -> PromptConfig:
        """
        Load prompt configuration from YAML
        從 YAML 載入 prompt 配置
        
        Args:
            name: Prompt name (without .yaml extension)
            version: Specific version to load (optional)
            reload: Force reload from disk
            
        Returns:
            PromptConfig object
        """
        cache_key = f"{name}:{version or 'latest'}"

        # Return cached if available
        if not reload and cache_key in self._cache:
            return self._cache[cache_key]

        # Find YAML file
        if version:
            yaml_path = self.prompts_dir / f"{name}.v{version}.yaml"
            if not yaml_path.exists():
                yaml_path = self.prompts_dir / f"{name}.{version}.yaml"
        else:
            yaml_path = self.prompts_dir / f"{name}.yaml"

        if not yaml_path.exists():
            raise FileNotFoundError(f"Prompt config not found: {yaml_path}")

        # Load and parse YAML
        logger.info(f"Loading prompt config: {yaml_path}")
        with open(yaml_path, encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)

        # Parse config
        config = self._parse_config(raw_config, yaml_path)

        # Cache and return
        self._cache[cache_key] = config
        return config

    def _parse_config(self, raw: dict[str, Any], source_path: Path) -> PromptConfig:
        """Parse raw YAML dict into PromptConfig"""

        # Parse metadata
        metadata = raw.get("metadata", {})

        # Parse PHI types
        phi_types = {}
        for name, type_data in raw.get("phi_types", {}).items():
            phi_types[name] = PHITypeConfig(
                name=name,
                description=type_data.get("description", ""),
                examples=type_data.get("examples", []),
                regex_patterns=type_data.get("regex_patterns", []),
                priority=type_data.get("priority", "medium"),
                special_rule=type_data.get("special_rule"),
            )

        # Parse prompts
        prompts = {}
        for name, prompt_data in raw.get("prompts", {}).items():
            prompts[name] = PromptTemplate(
                name=name,
                template=prompt_data.get("template", ""),
                variables=prompt_data.get("variables", []),
            )

        # Parse few-shot examples
        few_shot = []
        for ex in raw.get("few_shot_examples", []):
            few_shot.append(FewShotExample(
                input=ex.get("input", ""),
                output=ex.get("output", ""),
                note=ex.get("note"),
            ))

        # Parse optimization config
        opt_raw = raw.get("optimization", {})
        dspy_raw = opt_raw.get("dspy", {})
        optimization = OptimizationConfig(
            default_method=dspy_raw.get("default_method", "bootstrap_fewshot"),
            bootstrap_fewshot=dspy_raw.get("bootstrap_fewshot", {}),
            mipro=dspy_raw.get("mipro", {}),
            targets=opt_raw.get("targets", {}),
            weights=opt_raw.get("weights", {}),
        )

        # Parse model configs
        model_configs = {}
        for model_name, model_data in raw.get("model_configs", {}).items():
            model_configs[model_name] = ModelConfig(
                model_name=model_name,
                prompt_style=model_data.get("prompt_style", "simplified"),
                temperature=model_data.get("temperature", 0.1),
                max_tokens=model_data.get("max_tokens", 1024),
                use_cot=model_data.get("use_cot", False),
                notes=model_data.get("notes", ""),
            )

        return PromptConfig(
            name=metadata.get("name", source_path.stem),
            version=metadata.get("version", "1.0.0"),
            description=metadata.get("description", ""),
            author=metadata.get("author", ""),
            created_at=metadata.get("created_at"),
            updated_at=metadata.get("updated_at"),
            benchmark=metadata.get("benchmark", {}),
            phi_types=phi_types,
            prompts=prompts,
            few_shot_examples=few_shot,
            optimization=optimization,
            model_configs=model_configs,
            source_path=source_path,
        )

    def save(
        self,
        config: PromptConfig,
        path: str | Path | None = None,
    ) -> Path:
        """
        Save prompt configuration to YAML
        保存 prompt 配置到 YAML
        
        Args:
            config: PromptConfig to save
            path: Output path (default: prompts_dir/name.version.yaml)
            
        Returns:
            Path to saved file
        """
        if path is None:
            path = self.prompts_dir / f"{config.name}.v{config.version}.yaml"
        else:
            path = Path(path)

        # Update timestamp
        config.updated_at = datetime.now().strftime("%Y-%m-%d")

        # Convert to dict
        data = config.to_dict()

        # Save as YAML
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved prompt config to: {path}")
        return path

    def save_optimized(
        self,
        config: PromptConfig,
        new_version: str | None = None,
        benchmark_results: dict[str, Any] | None = None,
        new_examples: list[FewShotExample] | None = None,
    ) -> Path:
        """
        Save optimized prompt configuration with new version
        保存優化後的 prompt 配置並增加版本號
        
        Args:
            config: Original config
            new_version: New version string (auto-increment if None)
            benchmark_results: New benchmark results to record
            new_examples: New few-shot examples from optimization
            
        Returns:
            Path to saved file
        """
        # Auto-increment version if not specified
        if new_version is None:
            parts = config.version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            new_version = ".".join(parts)

        # Create new config
        new_config = PromptConfig(
            name=config.name,
            version=new_version,
            description=config.description + f"\n[Optimized from v{config.version}]",
            author=config.author,
            created_at=config.created_at,
            updated_at=datetime.now().strftime("%Y-%m-%d"),
            benchmark=benchmark_results or config.benchmark,
            phi_types=config.phi_types,
            prompts=config.prompts,
            few_shot_examples=new_examples or config.few_shot_examples,
            optimization=config.optimization,
            model_configs=config.model_configs,
        )

        return self.save(new_config)

    def list_prompts(self) -> list[dict[str, Any]]:
        """
        List all available prompts
        列出所有可用的 prompts
        
        Returns:
            List of dicts with name, version, description
        """
        prompts = []

        for yaml_file in self.prompts_dir.glob("*.yaml"):
            if yaml_file.name == "schema.yaml":
                continue

            try:
                with open(yaml_file, encoding="utf-8") as f:
                    raw = yaml.safe_load(f)

                metadata = raw.get("metadata", {})
                prompts.append({
                    "name": metadata.get("name", yaml_file.stem),
                    "version": metadata.get("version", "unknown"),
                    "description": metadata.get("description", "")[:100],
                    "file": yaml_file.name,
                })
            except Exception as e:
                logger.warning(f"Failed to read {yaml_file}: {e}")

        return prompts

    def validate(self, config: PromptConfig) -> list[str]:
        """
        Validate prompt configuration
        驗證 prompt 配置
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        if not config.name:
            errors.append("Missing required field: name")
        if not config.version:
            errors.append("Missing required field: version")
        if not config.prompts:
            errors.append("No prompt templates defined")

        # Validate version format
        if not re.match(r"^\d+\.\d+\.\d+$", config.version):
            errors.append(f"Invalid version format: {config.version} (expected: X.Y.Z)")

        # Validate prompts have templates
        for name, prompt in config.prompts.items():
            if not prompt.template:
                errors.append(f"Prompt '{name}' has empty template")

        # Validate few-shot examples
        for i, ex in enumerate(config.few_shot_examples):
            if not ex.input:
                errors.append(f"Few-shot example {i} has empty input")
            if not ex.output:
                errors.append(f"Few-shot example {i} has empty output")

        return errors


# Convenience function
def load_prompt_config(
    name: str = "phi_identification",
    version: str | None = None,
) -> PromptConfig:
    """
    Load prompt configuration (convenience function)
    載入 prompt 配置（便捷函數）
    
    Args:
        name: Prompt name
        version: Version string
        
    Returns:
        PromptConfig
    """
    manager = PromptManager()
    return manager.load(name, version)


# Export
__all__ = [
    "FewShotExample",
    "ModelConfig",
    "OptimizationConfig",
    "PHITypeConfig",
    "PromptConfig",
    "PromptManager",
    "PromptTemplate",
    "load_prompt_config",
]
