"""
Intent Classifier - Automatic per-message routing between CHAT and EDIT modes
Uses hybrid logic (keywords + LLM) to detect garment edit commands
"""

import os
import sys
import re
from typing import Dict, Tuple
from datetime import datetime

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
    import ollama
except ImportError:
    def log(msg, category="INTENT"):
        print(f"[{category}] {msg}")
    ollama = None

class IntentClassifier:
    """Classifies user intent as EDIT (garment modification) or CHAT (conversation)"""
    
    def __init__(self):
        self.log_file = os.path.join(BASE_DIR, "Logs", "clo_autorouter.log")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # EDIT intent keywords (actionable design commands)
        self.edit_keywords = [
            "make", "add", "change", "remove", "shorten", "lengthen",
            "color", "colour", "logo", "fabric", "material", "resize",
            "replace", "adjust", "modify", "edit", "update", "set",
            "increase", "decrease", "expand", "shrink", "widen", "narrow",
            "tighter", "looser", "fitted", "oversized", "longer", "shorter",
            "bigger", "smaller", "undo", "revert", "cuff", "sleeve", "hem",
            "collar", "belt", "hood", "pocket"
        ]
        
        # Strong EDIT indicators (always trigger EDIT)
        self.strong_edit_patterns = [
            r"make (sleeve|sleeves|logo|hem|fit|it)",
            r"(adjust|change|modify) (sleeve|color|colour|logo|fit|length|width)",
            r"(add|remove) (logo|belt|hood|cuff|collar|pocket)",
            r"(shorten|lengthen|widen|narrow) (sleeve|hem|collar)",
            r"(make|set) it (fitted|oversized|tighter|looser|longer|shorter)",
            r"resize (logo|sleeve)",
            r"undo|revert",
            r"v\d+|version \d+"
        ]
        
        # CHAT indicators (override if detected)
        self.chat_indicators = [
            r"what|how|why|when|where",
            r"explain|describe|tell me|inform",
            r"trend|trending|research|academic",
            r"idea|brainstorm|suggest|recommend",
            r"think|opinion|thought|believe",
            r"discuss|talk about|share"
        ]
        
        log("IntentClassifier initialized", "INTENT")
    
    def detect_intent(self, text: str) -> Tuple[str, float]:
        """
        Detect user intent: EDIT (garment modification) or CHAT (conversation)
        
        Args:
            text: User input text
        
        Returns:
            Tuple of (intent: "EDIT" or "CHAT", confidence: float 0.0-1.0)
        """
        text_lower = text.lower().strip()
        
        # Quick check: empty or very short
        if len(text_lower) < 3:
            return ("CHAT", 0.5)
        
        # Step 1: Check for strong EDIT patterns (high confidence)
        for pattern in self.strong_edit_patterns:
            if re.search(pattern, text_lower):
                self._log_intent("EDIT", text, 0.95, "strong_pattern")
                return ("EDIT", 0.95)
        
        # Step 2: Check for CHAT indicators (override to CHAT)
        for pattern in self.chat_indicators:
            if re.search(pattern, text_lower):
                self._log_intent("CHAT", text, 0.9, "chat_indicator")
                return ("CHAT", 0.9)
        
        # Step 3: Keyword matching
        keyword_matches = sum(1 for kw in self.edit_keywords if kw in text_lower)
        
        if keyword_matches >= 2:
            # Multiple keywords suggest EDIT intent
            confidence = min(0.85, 0.6 + (keyword_matches * 0.1))
            self._log_intent("EDIT", text, confidence, f"keyword_match_{keyword_matches}")
            return ("EDIT", confidence)
        elif keyword_matches == 1:
            # Single keyword - use LLM to confirm
            confidence = 0.65
            self._log_intent("EDIT", text, confidence, "single_keyword")
            return ("EDIT", confidence)
        
        # Step 4: Use LLM for ambiguous cases (if available)
        if ollama:
            llm_intent, llm_confidence = self._llm_classify(text)
            if llm_confidence > 0.6:
                self._log_intent(llm_intent, text, llm_confidence, "llm_classification")
                return (llm_intent, llm_confidence)
        
        # Default: CHAT (conservative - only switch to EDIT if clear)
        self._log_intent("CHAT", text, 0.5, "default")
        return ("CHAT", 0.5)
    
    def _llm_classify(self, text: str) -> Tuple[str, float]:
        """
        Use local LLM to classify intent
        
        Returns:
            Tuple of (intent, confidence)
        """
        try:
            prompt = f"""Decide if this message is a garment edit command (yes/no): "{text}"

A garment edit command:
- Asks to modify existing design (e.g., "make sleeves longer", "change color")
- Uses action verbs (make, change, add, remove, adjust)
- References design elements (sleeve, color, logo, fit, length)

NOT an edit command:
- Questions (what, how, why, explain)
- Research/brainstorming requests
- General conversation

Respond with ONLY:
- "yes" if it's an edit command
- "no" if it's not an edit command

Response:"""
            
            response = ollama.generate(
                model="llama3.2",
                prompt=prompt,
                options={
                    "temperature": 0.1,  # Very low for deterministic yes/no
                    "num_predict": 5  # Just need yes/no
                }
            )
            
            response_text = response.get("response", "").lower().strip()
            
            if "yes" in response_text:
                return ("EDIT", 0.75)
            elif "no" in response_text:
                return ("CHAT", 0.75)
            else:
                # Ambiguous response
                return ("CHAT", 0.5)
                
        except Exception as e:
            log(f"LLM classification failed: {e}", "INTENT", level="WARNING")
            return ("CHAT", 0.5)
    
    def _log_intent(self, intent: str, text: str, confidence: float, method: str):
        """Log intent detection decision"""
        try:
            timestamp = datetime.now().isoformat()
            text_excerpt = text[:50] + ("..." if len(text) > 50 else "")
            
            log_entry = f"[{timestamp}] [MODE:{intent}] [{text_excerpt}] [Confidence:{confidence:.2f}] [Method:{method}]\n"
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            log(f"Intent: {intent} (conf: {confidence:.2f}, method: {method}) | {text_excerpt}", "INTENT", print_to_console=False)
        except Exception as e:
            pass  # Don't fail if logging fails
    
    def confidence_score(self, text: str) -> float:
        """Get confidence score for intent detection (without full classification)"""
        _, confidence = self.detect_intent(text)
        return confidence
    
    def add_edit_keyword(self, keyword: str):
        """Add custom keyword to EDIT detector (for fine-tuning)"""
        if keyword.lower() not in self.edit_keywords:
            self.edit_keywords.append(keyword.lower())
            log(f"Added EDIT keyword: {keyword}", "INTENT")
    
    def record_false_positive(self, text: str, detected_intent: str, correct_intent: str):
        """Record a false positive/negative for future analysis"""
        try:
            log_entry = f"[{datetime.now().isoformat()}] [FALSE_POSITIVE] Detected:{detected_intent} Correct:{correct_intent} Text:{text}\n"
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            log(f"False positive recorded: {detected_intent} → {correct_intent}", "INTENT")
        except:
            pass

# Global instance
_intent_classifier_instance = None

def get_intent_classifier() -> IntentClassifier:
    """Get global intent classifier instance (singleton)"""
    global _intent_classifier_instance
    if _intent_classifier_instance is None:
        _intent_classifier_instance = IntentClassifier()
    return _intent_classifier_instance




