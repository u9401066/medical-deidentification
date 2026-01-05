"""
PHI Identification Agent | PHI 識別代理

Agent-based PHI identification where LLM decides when to use tools.
基於代理的 PHI 識別，由 LLM 決定何時使用工具。

Architecture:
    User Request → LLM Agent → [Decide] → Call Tools → Integrate Results
                                  ↓
                            [No tools needed] → Direct Response

This implements the ReAct (Reasoning + Acting) pattern where:
1. LLM analyzes the text
2. LLM decides if tools are needed (regex scan, ID validation, etc.)
3. LLM calls tools and integrates results
4. LLM provides final PHI identification

Benefits over pre-scanning approach:
- LLM decides intelligently based on text content
- Avoids unnecessary tool calls for simple cases
- Can request specific tools based on context
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from loguru import logger

from langchain_core.tools import tool, BaseTool, StructuredTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..llm.factory import create_llm
from ...domain import PHIEntity
from ...domain.phi_types import PHIType
from ...domain.phi_identification_models import (
    PHIIdentificationConfig,
    PHIIdentificationResult,
    PHIDetectionResponse,
)
from ..tools import ToolRunner, ToolResult, RegexPHITool, IDValidatorTool, PhoneTool


def create_phi_tools() -> List[BaseTool]:
    """
    Create LangChain tools from PHI detection tools
    將 PHI 檢測工具轉換為 LangChain 工具格式
    
    Returns:
        List of LangChain BaseTool instances
    """
    
    @tool
    def scan_for_patterns(text: str) -> str:
        """
        Scan text for PHI patterns using regex.
        Use this tool when you need to find:
        - Taiwan National IDs (身份證字號)
        - Email addresses
        - URLs
        - IP addresses
        - Dates in various formats
        
        Args:
            text: The medical text to scan
            
        Returns:
            JSON string with detected patterns
        """
        regex_tool = RegexPHITool()
        results = regex_tool.scan(text)
        
        if not results:
            return "No patterns found."
        
        # Format results for LLM
        findings = []
        for r in results:
            findings.append(f"- {r.phi_type.value}: '{r.text}' (confidence: {r.confidence:.0%})")
        
        return "Found patterns:\n" + "\n".join(findings)
    
    @tool
    def validate_taiwan_id(id_number: str) -> str:
        """
        Validate a Taiwan National ID number with checksum verification.
        Use this tool when you find something that looks like a Taiwan ID
        and want to confirm if it's valid.
        
        Args:
            id_number: The ID number to validate (e.g., A123456789)
            
        Returns:
            Validation result with ID type and validity
        """
        validator = IDValidatorTool()
        is_valid, id_type = validator.validate_id(id_number)
        
        return f"ID: {id_number}\nType: {id_type}\nValid checksum: {is_valid}"
    
    @tool
    def scan_phone_numbers(text: str) -> str:
        """
        Scan text for phone numbers (Taiwan format).
        Use this tool to find:
        - Mobile numbers (09XX-XXX-XXX)
        - Landline numbers (0X-XXXX-XXXX)
        - International format (+886-X-XXXX-XXXX)
        - Fax numbers (when context indicates fax)
        
        Args:
            text: The medical text to scan
            
        Returns:
            List of detected phone numbers with types
        """
        phone_tool = PhoneTool()
        results = phone_tool.scan(text)
        
        if not results:
            return "No phone numbers found."
        
        findings = []
        for r in results:
            phone_type = r.metadata.get("phone_type", "UNKNOWN")
            findings.append(f"- {r.text} ({phone_type}, confidence: {r.confidence:.0%})")
        
        return "Found phone numbers:\n" + "\n".join(findings)
    
    @tool
    def scan_all_phi(text: str) -> str:
        """
        Run all PHI detection tools at once.
        Use this tool for comprehensive scanning when you want to find
        all types of PHI in the text at once.
        
        Args:
            text: The medical text to scan
            
        Returns:
            All detected PHI organized by type
        """
        runner = ToolRunner.create_default()
        results = runner.run_all(text)
        
        if not results:
            return "No PHI patterns detected by tools."
        
        # Group by PHI type
        grouped: Dict[str, List[ToolResult]] = {}
        for r in results:
            phi_type = r.phi_type.value if hasattr(r.phi_type, 'value') else str(r.phi_type)
            if phi_type not in grouped:
                grouped[phi_type] = []
            grouped[phi_type].append(r)
        
        # Format output
        lines = ["PHI Detection Results:"]
        for phi_type, type_results in grouped.items():
            lines.append(f"\n{phi_type}:")
            for r in type_results:
                lines.append(f"  - '{r.text}' at position {r.start_pos}-{r.end_pos} (confidence: {r.confidence:.0%})")
        
        return "\n".join(lines)
    
    return [scan_for_patterns, validate_taiwan_id, scan_phone_numbers, scan_all_phi]


class PHIIdentificationAgent:
    """
    Agent for PHI identification with tool-calling capability
    具有工具呼叫能力的 PHI 識別代理
    
    The LLM decides when and which tools to use based on the text content.
    LLM 根據文本內容決定何時使用哪些工具。
    
    Examples:
        >>> agent = PHIIdentificationAgent()
        >>> 
        >>> # Simple text - LLM may not need tools
        >>> result = agent.identify_phi("患者王先生今日就診")
        >>> 
        >>> # Complex text - LLM will likely use tools
        >>> result = agent.identify_phi(
        ...     "患者張三，身份證 A123456789，電話 0912-345-678"
        ... )
    """
    
    SYSTEM_PROMPT = """You are a PHI (Protected Health Information) identification expert.
Your task is to identify all PHI entities in medical text that need to be de-identified.

你是一位 PHI（受保護健康資訊）識別專家。
你的任務是識別醫療文本中所有需要去識別化的 PHI 實體。

PHI types to identify (需要識別的 PHI 類型):
- NAME: Patient names, doctor names, family member names (姓名)
- ID: National IDs, medical record numbers, account numbers (識別碼)
- DATE: Dates except year (日期，年份除外)
- PHONE: Phone numbers, fax numbers (電話號碼)
- EMAIL: Email addresses (電子郵件)
- LOCATION: Addresses, hospital names, ward numbers (地點)
- AGE_OVER_89: Ages over 89 years old (超過89歲的年齡)

You have access to tools that can help you:
- scan_for_patterns: Quick regex scan for common PHI patterns
- validate_taiwan_id: Validate Taiwan ID checksums
- scan_phone_numbers: Find phone/fax numbers
- scan_all_phi: Comprehensive scan with all tools

Strategy (策略):
1. First analyze the text to understand what types of PHI might be present
2. Use tools when you see patterns that need validation (e.g., ID-like numbers)
3. Combine tool results with your own analysis
4. Report ALL PHI found, including those tools might have missed (like names)

Always output your final answer in this JSON format:
{
    "entities": [
        {"text": "...", "type": "NAME|ID|DATE|PHONE|EMAIL|LOCATION|...", "confidence": 0.0-1.0, "reasoning": "..."}
    ]
}
"""
    
    def __init__(
        self,
        config: Optional[PHIIdentificationConfig] = None,
        max_iterations: int = 5,
    ):
        """
        Initialize PHI identification agent
        
        Args:
            config: Configuration for LLM
            max_iterations: Maximum tool-calling iterations (default: 5)
        """
        self.config = config or PHIIdentificationConfig()
        self.max_iterations = max_iterations
        
        # Initialize LLM
        self.llm = create_llm(self.config.llm_config)
        
        # Create tools
        self.tools = create_phi_tools()
        
        # Bind tools to LLM (if supported)
        try:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
            self._supports_tool_calling = True
            logger.info(f"PHI Agent initialized with {len(self.tools)} tools (tool-calling enabled)")
        except (AttributeError, NotImplementedError):
            self._supports_tool_calling = False
            self.llm_with_tools = self.llm
            logger.warning("LLM does not support tool-calling, falling back to prompt-based approach")
        
        # Build prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ])
    
    def identify_phi(
        self,
        text: str,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Identify PHI in medical text using agent with tools
        使用代理和工具識別醫療文本中的 PHI
        
        Args:
            text: Medical text to analyze
            language: Language hint (optional)
            
        Returns:
            Dictionary with entities and metadata
        """
        logger.info(f"Agent identifying PHI in text ({len(text)} chars)")
        
        # Build initial message
        user_message = f"Please identify all PHI in the following medical text:\n\n{text}"
        if language:
            user_message = f"[Language: {language}]\n\n{user_message}"
        
        messages: List[Any] = [HumanMessage(content=user_message)]
        response = None  # Initialize response for type checker
        
        # Agent loop
        for iteration in range(self.max_iterations):
            logger.debug(f"Agent iteration {iteration + 1}/{self.max_iterations}")
            
            # Get LLM response
            response = self.llm_with_tools.invoke(
                self.prompt.invoke({"messages": messages})
            )
            
            messages.append(response)
            
            # Check if LLM wants to call tools
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Execute tool calls
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    logger.debug(f"Agent calling tool: {tool_name}")
                    
                    # Find and execute tool
                    tool_result = self._execute_tool(tool_name, tool_args)
                    
                    # Add tool result to messages
                    messages.append(ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call["id"],
                    ))
            else:
                # No more tool calls - LLM is done
                logger.debug("Agent finished (no more tool calls)")
                break
        
        # Parse final response
        if response is None:
            logger.error("No response from agent")
            return self._parse_response("", text, language)
        
        return self._parse_response(response.content, text, language)
    
    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Execute a tool by name"""
        for tool in self.tools:
            if tool.name == tool_name:
                try:
                    return tool.invoke(tool_args)
                except Exception as e:
                    logger.error(f"Tool {tool_name} failed: {e}")
                    return f"Tool error: {str(e)}"
        
        return f"Unknown tool: {tool_name}"
    
    def _parse_response(
        self, 
        response_text: str, 
        original_text: str,
        language: Optional[str]
    ) -> Dict[str, Any]:
        """Parse LLM response to extract PHI entities"""
        import json
        import re
        
        entities = []
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*"entities"[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group(0))
                raw_entities = data.get("entities", [])
                
                for e in raw_entities:
                    # Convert to PHIEntity
                    phi_type_str = e.get("type", "OTHER")
                    try:
                        phi_type = PHIType(phi_type_str)
                    except ValueError:
                        phi_type = PHIType.OTHER
                    
                    entity_text = e.get("text", "")
                    start_pos = original_text.find(entity_text)
                    entity = PHIEntity(
                        type=phi_type,
                        text=entity_text,
                        start_pos=start_pos if start_pos >= 0 else 0,
                        end_pos=start_pos + len(entity_text) if start_pos >= 0 else len(entity_text),
                        confidence=e.get("confidence", 0.8),
                    )
                    entities.append(entity)
                    
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse agent response: {e}")
        
        return {
            "text": original_text,
            "language": language or "unknown",
            "total_entities": len(entities),
            "has_phi": len(entities) > 0,
            "entities": entities,
            "agent_response": response_text,
        }
