"""
Semantic Auto-Tagging Module
Automatically classifies documents with semantic tags using Llama 3
"""

import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Configuration
OLLAMA_MODEL = "llama3.2"
TAGS_LOG = os.path.join(os.path.dirname(__file__), "Logs", "tags.log")
MAX_TAGS_PER_DOC = 5

# Predefined academic topics (for consistent tagging)
ACADEMIC_TOPICS = [
    "Strategic Management", "Organizational Behavior", "Leadership",
    "Entrepreneurship", "Innovation", "Blue Economy", "Sustainability",
    "Corporate Governance", "Business Ethics", "Marketing Strategy",
    "Operations Management", "Supply Chain", "Finance", "Accounting",
    "Human Resources", "Change Management", "Project Management",
    "Risk Management", "Information Systems", "Technology Management",
    "International Business", "Economics", "Management Theory",
    "Organizational Theory", "Decision Making", "Communication",
    "Team Management", "Conflict Resolution", "Negotiation",
    "Sensemaking", "Organizational Learning", "Knowledge Management"
]

def classify_document(text, existing_tags=None):
    """
    Classify document and return semantic tags
    
    Args:
        text: Document text to classify
        existing_tags: Optional existing tags to consider
        
    Returns:
        List of tag strings (3-5 tags)
    """
    if not text or len(text.strip()) < 50:
        return ["Uncategorized"]
    
    # Limit text size for efficiency (first 3000 chars)
    text_preview = text[:3000].strip()
    
    # Build prompt for zero-shot classification
    topics_list = ", ".join(ACADEMIC_TOPICS[:20])  # Top 20 for prompt
    
    prompt = f"""Analyze the following academic document and identify 3-5 main topics/themes.

AVAILABLE TOPICS (use these or suggest others if more appropriate):
{topics_list}

DOCUMENT TEXT:
{text_preview}

INSTRUCTIONS:
1. Identify 3-5 main topics/themes from the document
2. Use topics from the list above when possible
3. If none match, suggest appropriate new topics
4. Return only topic names, one per line, no explanations
5. Use clear, concise topic names

TOPICS:"""
    
    try:
        # Call Ollama with Llama 3.2
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL, prompt],
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8"
        )
        
        if result.returncode == 0:
            # Parse response
            response = result.stdout.strip()
            
            # Extract tags (one per line, filtered)
            tags = []
            for line in response.split('\n'):
                tag = line.strip()
                # Remove common prefixes/suffixes
                tag = tag.replace('Topic:', '').replace('-', '').strip()
                tag = tag.split(':')[0].strip() if ':' in tag else tag
                tag = tag.split('.')[0].strip() if tag and tag[0].isdigit() else tag
                
                if tag and len(tag) > 2 and len(tag) < 50:
                    # Capitalize properly
                    tag = ' '.join(word.capitalize() for word in tag.split())
                    if tag not in tags:
                        tags.append(tag)
            
            # Ensure 3-5 tags
            if len(tags) < 3:
                # Add generic tags
                tags.extend(["Academic Document", "Management Studies"])
            elif len(tags) > MAX_TAGS_PER_DOC:
                tags = tags[:MAX_TAGS_PER_DOC]
            
            return tags[:MAX_TAGS_PER_DOC]
        else:
            return ["Auto-Tagging Failed"]
    
    except subprocess.TimeoutExpired:
        return ["Processing Timeout"]
    except Exception as e:
        return [f"Error: {str(e)[:30]}"]

def tag_document(document_path, document_text, metadata=None):
    """
    Tag a document and update metadata
    
    Args:
        document_path: Path to the document
        document_text: Text content of the document
        metadata: Existing metadata dict (will be updated)
        
    Returns:
        Updated metadata dict with tags
    """
    if metadata is None:
        metadata = {}
    
    # Get tags
    existing_tags = metadata.get('tags', [])
    tags = classify_document(document_text, existing_tags)
    
    # Update metadata
    metadata['tags'] = tags
    metadata['tagged_date'] = datetime.now().isoformat()
    metadata['tagged_model'] = OLLAMA_MODEL
    
    # Log tags
    log_tags(document_path, tags)
    
    return metadata, tags

def log_tags(document_path, tags):
    """Log tags to file"""
    os.makedirs(os.path.dirname(TAGS_LOG), exist_ok=True)
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'document': os.path.basename(document_path),
        'path': document_path,
        'tags': tags
    }
    
    try:
        with open(TAGS_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        print(f"Failed to log tags: {e}")

def get_tags_for_document(document_path):
    """Get tags for a specific document from log"""
    if not os.path.exists(TAGS_LOG):
        return []
    
    try:
        with open(TAGS_LOG, 'r', encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line.strip())
                if entry.get('path') == document_path or os.path.basename(entry.get('path', '')) == os.path.basename(document_path):
                    return entry.get('tags', [])
    except Exception as e:
        print(f"Error reading tags log: {e}")
    
    return []

def get_all_tags():
    """Get all unique tags from the log"""
    if not os.path.exists(TAGS_LOG):
        return []
    
    all_tags = set()
    try:
        with open(TAGS_LOG, 'r', encoding='utf-8') as f:
            for line in f:
                entry = json.loads(line.strip())
                tags = entry.get('tags', [])
                all_tags.update(tags)
    except Exception as e:
        print(f"Error reading tags: {e}")
    
    return sorted(list(all_tags))

def retag_all_documents(vault_path):
    """Re-tag all documents in the vault"""
    from index_documents import extract_text_from_file
    
    notes_path = os.path.join(vault_path, "Notes")
    if not os.path.exists(notes_path):
        print(f"Notes path not found: {notes_path}")
        return
    
    tagged_count = 0
    for root, dirs, files in os.walk(notes_path):
        for file in files:
            if file.endswith(('.md', '.txt')):
                file_path = os.path.join(root, file)
                try:
                    text = extract_text_from_file(file_path)
                    if text:
                        tags = classify_document(text)
                        log_tags(file_path, tags)
                        tagged_count += 1
                        print(f"Tagged: {os.path.basename(file_path)} -> {', '.join(tags)}")
                except Exception as e:
                    print(f"Error tagging {file_path}: {e}")
    
    print(f"\nTagged {tagged_count} documents")

if __name__ == "__main__":
    # Test with sample text
    sample_text = """
    Strategic management is the process of specifying an organization's objectives,
    developing policies and plans to achieve these objectives, and allocating
    resources to implement the plans. Strategic management provides overall
    direction to the enterprise and involves specifying the organization's
    mission, vision and objectives, developing policies and plans, often in terms
    of projects and programs, which are designed to achieve these objectives, and
    then allocating resources to implement the policies and plans, projects and programs.
    """
    
    tags = classify_document(sample_text)
    print(f"Sample tags: {', '.join(tags)}")




