"""
Centralized prompt templates for LLM interactions.

Provides reusable system and user prompts with configurable options.
"""

from typing import List, Dict

# System prompts
SYSTEM_RAG = """You are a precise and helpful assistant. Your task is to answer questions based ONLY on the provided context documents.

Rules:
1. Ground all answers in the provided context
2. If the context doesn't contain enough information, say so clearly
3. Be concise but complete
4. Maintain a professional, informative tone
5. Do not make up information beyond what's in the context"""

SYSTEM_RAG_WITH_CITATIONS = """You are a precise and helpful assistant. Your task is to answer questions based ONLY on the provided context documents.

Rules:
1. Ground all answers in the provided context
2. Cite sources using [Source: Context N] format
3. If the context doesn't contain enough information, say so clearly
4. Be concise but complete
5. Maintain a professional, informative tone
6. Do not make up information beyond what's in the context"""

SYSTEM_GENERAL = """You are a helpful, knowledgeable assistant. Provide clear, accurate, and well-structured responses."""

SYSTEM_SUMMARIZE = """You are an expert at summarization. Create concise, accurate summaries that capture the key points while maintaining important details."""

SYSTEM_ANALYSIS = """You are an analytical assistant. Break down complex topics into clear components, identify patterns, and provide structured insights."""


def build_rag_messages(question: str, contexts: List[str], 
                       citations: bool = False,
                       system_prompt: str = None) -> List[Dict[str, str]]:
    """
    Build messages for RAG query with context.
    
    Args:
        question: User's question
        contexts: List of context chunks
        citations: Whether to request citations in answer
        system_prompt: Optional custom system prompt
    
    Returns:
        List of message dictionaries for LLM
    """
    # Select system prompt
    if system_prompt is None:
        system_prompt = SYSTEM_RAG_WITH_CITATIONS if citations else SYSTEM_RAG
    
    # Build context section
    context_text = "\n\n---\n\n".join([
        f"Context {i+1}:\n{ctx}" 
        for i, ctx in enumerate(contexts)
    ])
    
    # Build user message
    user_message = f"""Context Documents:

{context_text}

---

Question: {question}

Please answer based on the context above."""
    
    if citations:
        user_message += " Include citations to specific context sections."
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]


def build_summarize_messages(text: str, length: str = "medium") -> List[Dict[str, str]]:
    """
    Build messages for summarization task.
    
    Args:
        text: Text to summarize
        length: Desired summary length (short, medium, long)
    
    Returns:
        List of message dictionaries
    """
    length_instructions = {
        "short": "Create a brief summary in 2-3 sentences.",
        "medium": "Create a comprehensive summary in 1-2 paragraphs.",
        "long": "Create a detailed summary covering all key points in 3-4 paragraphs."
    }
    
    instruction = length_instructions.get(length, length_instructions["medium"])
    
    user_message = f"""{instruction}

Text to summarize:

{text}"""
    
    return [
        {"role": "system", "content": SYSTEM_SUMMARIZE},
        {"role": "user", "content": user_message}
    ]


def build_analysis_messages(text: str, analysis_type: str = "general") -> List[Dict[str, str]]:
    """
    Build messages for analysis task.
    
    Args:
        text: Text to analyze
        analysis_type: Type of analysis (general, technical, comparative)
    
    Returns:
        List of message dictionaries
    """
    analysis_instructions = {
        "general": "Analyze the following text and provide key insights:",
        "technical": "Provide a technical analysis of the following text:",
        "comparative": "Compare and contrast the main ideas in the following text:"
    }
    
    instruction = analysis_instructions.get(analysis_type, analysis_instructions["general"])
    
    return [
        {"role": "system", "content": SYSTEM_ANALYSIS},
        {"role": "user", "content": f"{instruction}\n\n{text}"}
    ]


def build_chat_messages(user_input: str, system_prompt: str = None) -> List[Dict[str, str]]:
    """
    Build messages for general chat.
    
    Args:
        user_input: User's message
        system_prompt: Optional custom system prompt
    
    Returns:
        List of message dictionaries
    """
    system = system_prompt or SYSTEM_GENERAL
    
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_input}
    ]

