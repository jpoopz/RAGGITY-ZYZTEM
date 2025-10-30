"""
Helper script to call RAG API from command line
Makes it easier to use from Obsidian
"""

import sys
import requests
import json

API_BASE = "http://127.0.0.1:5000"

def call_api(endpoint, data):
    """Call RAG API endpoint"""
    try:
        response = requests.post(
            f"{API_BASE}/{endpoint}",
            json=data,
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: API server not running. Start it with: python rag_api.py", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

def query(query_text, use_web=False, reasoning_mode="Analytical"):
    """Query RAG system"""
    result = call_api("query", {
        "query": query_text,
        "use_web": use_web,
        "reasoning_mode": reasoning_mode
    })
    print(result["response"])
    if result.get("sources"):
        print("\n---\nCitations:", file=sys.stderr)
        for i, src in enumerate(result["sources"], 1):
            print(f"{i}. {src['source']} (lines {src.get('lines', 'N/A')})", file=sys.stderr)

def reindex():
    """Trigger re-indexing"""
    result = call_api("reindex", {})
    print(result.get("message", "Indexing triggered"), file=sys.stderr)
    if result.get("output"):
        print(result["output"], file=sys.stderr)

def summarize(file_path=None, text=None, length="medium"):
    """Summarize file or text"""
    data = {"length": length}
    if file_path:
        data["file_path"] = file_path
    elif text:
        data["text"] = text
    
    result = call_api("summarize", data)
    print(result["summary"])
    print(f"\n[Source: {result['source']}]", file=sys.stderr)

def plan_essay(topic, essay_type="academic"):
    """Create essay plan"""
    result = call_api("plan_essay", {
        "topic": topic,
        "type": essay_type
    })
    print(result["plan"])
    if result.get("sources"):
        print("\n---\nKey Sources:", file=sys.stderr)
        for src in result["sources"][:5]:
            print(f"  - {src['source']} (lines {src.get('lines', 'N/A')})", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python query_helper.py query 'your question'")
        print("  python query_helper.py reindex")
        print("  python query_helper.py summarize file_path")
        print("  python query_helper.py plan 'essay topic'")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "query":
        query_text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else input("Enter query: ")
        use_web = "--web" in sys.argv or "-w" in sys.argv
        reasoning_mode = "Analytical"
        if "--concise" in sys.argv or "-c" in sys.argv:
            reasoning_mode = "Concise"
        elif "--creative" in sys.argv:
            reasoning_mode = "Creative Academic"
        query(query_text, use_web, reasoning_mode)
    
    elif command == "reindex":
        reindex()
    
    elif command == "summarize":
        if len(sys.argv) < 3:
            print("Error: File path required", file=sys.stderr)
            sys.exit(1)
        file_path = sys.argv[2]
        length = sys.argv[3] if len(sys.argv) > 3 else "medium"
        summarize(file_path=file_path, length=length)
    
    elif command == "plan":
        if len(sys.argv) < 3:
            print("Error: Topic required", file=sys.stderr)
            sys.exit(1)
        topic = " ".join(sys.argv[2:])
        essay_type = "academic"
        if "--argumentative" in sys.argv:
            essay_type = "argumentative"
        elif "--analytical" in sys.argv:
            essay_type = "analytical"
        plan_essay(topic, essay_type)
    
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)




