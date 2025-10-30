"""
Feedback Interpreter - Parses natural language feedback into structured edit commands
Uses Llama 3.2 (Ollama) to interpret user feedback and generate JSON commands
"""

import os
import sys
import json
import re
from typing import Dict, Optional, List

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
    import ollama
except ImportError:
    def log(msg, category="CLO"):
        print(f"[{category}] {msg}")
    ollama = None

try:
    from modules.clo_companion.mode_manager import get_mode_manager
    from modules.clo_companion.prompt_router import get_prompt_router
except ImportError:
    get_mode_manager = None
    get_prompt_router = None

class FeedbackInterpreter:
    """Interprets natural language feedback into structured edit commands"""
    
    def __init__(self):
        self.model = "llama3.2"
        self.mode_manager = get_mode_manager() if get_mode_manager else None
        self.prompt_router = get_prompt_router() if get_prompt_router else None
        self.supported_actions = [
            "adjust_sleeve_length",
            "adjust_hem_length",
            "change_color",
            "change_material",
            "resize_logo",
            "add_logo",
            "remove_logo",
            "adjust_fit",
            "adjust_width",
            "adjust_length",
            "change_neckline",
            "add_belt",
            "remove_belt"
        ]
        
        log("FeedbackInterpreter initialized", "CLO")
    
    def interpret(self, feedback: str, current_context: Optional[Dict] = None) -> Dict:
        """
        Interpret natural language feedback into structured edit commands
        
        Args:
            feedback: User feedback text (e.g., "make sleeves longer")
            current_context: Optional context about current design
        
        Returns:
            Dict with keys: action, value, confidence, is_new_generation, mode
        """
        try:
            # Detect mode from input
            mode = "CHAT"
            if self.mode_manager:
                mode = self.mode_manager.detect_mode_from_input(feedback)
            
            # Check if this is clearly a new generation request
            if self._is_new_generation_request(feedback):
                return {
                    "action": "new_generation",
                    "value": feedback,
                    "confidence": 1.0,
                    "is_new_generation": True,
                    "commands": [],
                    "mode": mode
                }
            
            # Use Ollama to parse feedback
            if ollama is None:
                log("Ollama not available, using fallback parsing", "CLO", level="WARNING")
                result = self._fallback_parse(feedback)
                result["mode"] = mode
                return result
            
            # Get system prompt from router
            system_prompt = ""
            max_tokens = 500  # Default
            if self.prompt_router:
                system_prompt = self.prompt_router.get_prompt(mode)
                if mode == "CLO_WIZARD":
                    max_tokens = 200  # Limit output for structured JSON
            
            # Build prompt for Llama
            prompt = self._build_interpretation_prompt(feedback, current_context, system_prompt, mode)
            
            # Call Ollama
            options = {
                "temperature": 0.2 if mode == "CLO_WIZARD" else 0.3,  # Lower for structured output
                "top_p": 0.9
            }
            
            if mode == "CLO_WIZARD":
                options["num_predict"] = max_tokens  # Limit tokens
            
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options=options
            )
            
            response_text = response.get("response", "").strip()
            
            # Parse JSON from response
            try:
                # Extract JSON from response (may have extra text)
                json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                else:
                    # Try parsing entire response
                    parsed = json.loads(response_text)
                
                # Validate structure
                if isinstance(parsed, dict):
                    parsed["is_new_generation"] = parsed.get("is_new_generation", False)
                    parsed["confidence"] = parsed.get("confidence", 0.7)
                    parsed["mode"] = mode
                    
                    # For CLO_WIZARD mode, ensure commands are present
                    if mode == "CLO_WIZARD" and "commands" not in parsed:
                        # Try to construct commands from action/value
                        if "action" in parsed:
                            parsed["commands"] = [{"action": parsed.get("action"), 
                                                  "value": parsed.get("value", "")}]
                    
                    action = parsed.get('action', 'unknown')
                    value = parsed.get('value', '')
                    log(f"Interpreted feedback ({mode}): {action} = {value}", "CLO")
                    return parsed
                else:
                    raise ValueError("Invalid response structure")
                    
            except json.JSONDecodeError:
                log(f"Failed to parse JSON from Ollama response: {response_text}", "CLO", level="WARNING")
                
                # Auto-retry for CLO_WIZARD mode with constraint reminder
                if mode == "CLO_WIZARD" and ollama:
                    log("Retrying with JSON constraint reminder", "CLO", level="WARNING")
                    retry_prompt = prompt + "\n\nRemember: You must output ONLY valid JSON. No additional text."
                    try:
                        retry_response = ollama.generate(model=self.model, prompt=retry_prompt, options=options)
                        retry_text = retry_response.get("response", "").strip()
                        json_match = re.search(r'\{[^}]+\}', retry_text, re.DOTALL)
                        if json_match:
                            parsed = json.loads(json_match.group())
                            parsed["mode"] = mode
                            parsed["confidence"] = 0.6  # Lower confidence after retry
                            log("Retry successful", "CLO")
                            return parsed
                    except:
                        pass
                
                # Fallback
                result = self._fallback_parse(feedback)
                result["mode"] = mode
                return result
                
        except Exception as e:
            log(f"Error interpreting feedback: {e}", "CLO", level="ERROR")
            result = self._fallback_parse(feedback)
            result["mode"] = mode
            return result
    
    def _build_interpretation_prompt(self, feedback: str, context: Optional[Dict] = None,
                                   system_prompt: str = "", mode: str = "CHAT") -> str:
        """Build prompt for Llama to interpret feedback"""
        
        # Start with system prompt if provided
        prompt_parts = []
        if system_prompt:
            prompt_parts.append(system_prompt)
        
        context_str = ""
        if context:
            context_str = f"\nCurrent design:\n- File: {context.get('current_file', 'unknown')}\n- Attributes: {json.dumps(context.get('attributes', {}), indent=2)}\n- Last prompt: {context.get('last_prompt', 'none')}\n"
        
        # Build mode-specific prompt
        if mode == "CLO_WIZARD":
            # CLO_WIZARD mode: structured JSON output
            prompt_base = f"""{system_prompt if system_prompt else "You are CLO WIZARD."}

User feedback: "{feedback}"
{context_str}

Your task: Return ONLY valid JSON in this exact format:
{{
  "mode": "CLO_WIZARD",
  "commands": [
    {{"action": "adjust_sleeve_length", "value": "+2.5", "unit": "cm"}}
  ]
}}

Available actions:
{json.dumps(self.supported_actions, indent=2)}

Rules:
- Output ONLY JSON, no explanation
- Multiple commands can be in array
- If unclear, use generic_feedback action

Now parse this feedback:
"""
        else:
            # CHAT mode: conversational interpretation
            prompt_base = f"""{system_prompt if system_prompt else "You are a design assistant."}

User feedback: "{feedback}"
{context_str}

Your task: Determine if this is:
1. An iteration request (modifying existing garment): Return edit commands
2. A new generation request (completely new garment): Mark as new_generation

Available actions:
{json.dumps(self.supported_actions, indent=2)}

Return ONLY valid JSON in this exact format:
{{
  "action": "adjust_sleeve_length",
  "value": "+2.5cm",
  "commands": [
    {{"action": "adjust_sleeve_length", "value": "+2.5", "unit": "cm"}}
  ],
  "confidence": 0.9,
  "is_new_generation": false
}}

Rules:
- If user says "make a" or "create a" → is_new_generation: true
- If user gives specific measurements → include unit (cm, %, pixels)
- If user says "longer/bigger/more" → use positive values
- If user says "shorter/smaller/less" → use negative values
- Multiple commands can be in "commands" array
- Confidence: 0.0-1.0 (how certain you are)

Examples:
User: "make sleeves longer"
→ {{"action": "adjust_sleeve_length", "value": "+2.5cm", "commands": [{{"action": "adjust_sleeve_length", "value": "+2.5", "unit": "cm"}}], "confidence": 0.95, "is_new_generation": false}}

User: "make a denim jacket"
→ {{"action": "new_generation", "value": "denim jacket", "is_new_generation": true, "commands": [], "confidence": 1.0}}

User: "change color to black"
→ {{"action": "change_color", "value": "black", "commands": [{{"action": "change_color", "value": "#000000"}}], "confidence": 0.9, "is_new_generation": false}}

Now parse this feedback:
"""
        
        return prompt_base
    
    def _is_new_generation_request(self, feedback: str) -> bool:
        """Quick check if feedback is clearly a new generation request"""
        feedback_lower = feedback.lower()
        
        new_gen_keywords = [
            "make a", "create a", "generate a", "design a", "new",
            "i want a", "give me a", "i need a"
        ]
        
        for keyword in new_gen_keywords:
            if keyword in feedback_lower and len(feedback.split()) > 3:  # Not just "make a" alone
                return True
        
        return False
    
    def _fallback_parse(self, feedback: str) -> Dict:
        """Fallback parsing using keyword matching when Ollama unavailable"""
        feedback_lower = feedback.lower()
        
        # Sleeve adjustments
        if "sleeve" in feedback_lower:
            if "longer" in feedback_lower or "long" in feedback_lower:
                return {
                    "action": "adjust_sleeve_length",
                    "value": "+2.5cm",
                    "commands": [{"action": "adjust_sleeve_length", "value": "+2.5", "unit": "cm"}],
                    "confidence": 0.7,
                    "is_new_generation": False,
                    "mode": "CLO_WIZARD"
                }
            elif "shorter" in feedback_lower or "short" in feedback_lower:
                return {
                    "action": "adjust_sleeve_length",
                    "value": "-2.5cm",
                    "commands": [{"action": "adjust_sleeve_length", "value": "-2.5", "unit": "cm"}],
                    "confidence": 0.7,
                    "is_new_generation": False,
                    "mode": "CLO_WIZARD"
                }
        
        # Color changes
        if "color" in feedback_lower or "colour" in feedback_lower:
            color_map = {
                "black": "#000000",
                "white": "#FFFFFF",
                "red": "#FF0000",
                "blue": "#0000FF",
                "navy": "#000080",
                "beige": "#F5F5DC"
            }
            
            for color_name, hex_code in color_map.items():
                if color_name in feedback_lower:
                    return {
                        "action": "change_color",
                        "value": color_name,
                        "commands": [{"action": "change_color", "value": hex_code}],
                        "confidence": 0.7,
                        "is_new_generation": False,
                        "mode": "CLO_WIZARD"
                    }
        
        # Material changes
        if "material" in feedback_lower or "fabric" in feedback_lower:
            materials = ["cotton", "denim", "leather", "silk", "wool"]
            for mat in materials:
                if mat in feedback_lower:
                    return {
                        "action": "change_material",
                        "value": mat,
                        "commands": [{"action": "change_material", "value": mat}],
                        "confidence": 0.7,
                        "is_new_generation": False,
                        "mode": "CLO_WIZARD"
                    }
        
        # Default: assume it's feedback but parse as generic adjustment
        return {
            "action": "adjust_fit",
            "value": feedback,
            "commands": [{"action": "generic_feedback", "value": feedback}],
            "confidence": 0.5,
            "is_new_generation": False,
            "mode": "CHAT"  # Default to CHAT for fallback
        }
    
    def merge_commands(self, commands: List[Dict]) -> List[Dict]:
        """Merge multiple edit commands, removing duplicates and conflicts"""
        merged = []
        seen_actions = set()
        
        for cmd in commands:
            action = cmd.get("action", "")
            if action not in seen_actions:
                merged.append(cmd)
                seen_actions.add(action)
            else:
                # Replace earlier command with same action
                merged = [c for c in merged if c.get("action") != action]
                merged.append(cmd)
        
        return merged

