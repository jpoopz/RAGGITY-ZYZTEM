"""
Web Search Function with Rate Limiting and Logging
Uses Cursor bridge client for web retrieval
"""

import time
from typing import Dict, Any, List
from logger import get_logger

log = get_logger("web_search")

# Rate limiting state
_last_request_time = 0
_min_delay_seconds = 0.5  # 500ms minimum between calls


def web_search(query: str, max_results: int = 5, retry_count: int = 3) -> Dict[str, Any]:
    """
    Perform web search with rate limiting, retry logic, and request/response logging
    
    Args:
        query: Search query string
        max_results: Maximum number of results (default: 5)
        retry_count: Number of retry attempts on failure (default: 3)
        
    Returns:
        Dictionary with:
            - results: List of search results
            - query: Original query
            - count: Number of results
            - error: Error message if failed
    """
    global _last_request_time
    
    # Rate limiting - enforce minimum delay between calls
    current_time = time.time()
    time_since_last = current_time - _last_request_time
    
    if time_since_last < _min_delay_seconds:
        sleep_time = _min_delay_seconds - time_since_last
        log.info(f"Rate limiting: sleeping {sleep_time:.2f}s")
        time.sleep(sleep_time)
    
    _last_request_time = time.time()
    
    # Log request (truncate long queries)
    query_display = query[:100] + "..." if len(query) > 100 else query
    log.info(f"Web search request: '{query_display}' (max_results={max_results})")
    
    # Import client
    try:
        from modules.cursor_bridge.client import get_cursor_bridge_client
        client = get_cursor_bridge_client()
    except ImportError as e:
        log.error(f"Failed to import Cursor bridge client: {e}")
        return {
            "error": "Cursor bridge client not available",
            "results": [],
            "query": query,
            "count": 0
        }
    
    # Retry loop with exponential backoff
    last_error = None
    
    for attempt in range(1, retry_count + 1):
        try:
            log.info(f"Search attempt {attempt}/{retry_count}")
            
            # Make request
            response = client.search(query, max_results=max_results)
            
            # Check for error in response
            if "error" in response and not response.get("results"):
                last_error = response["error"]
                log.warning(f"Attempt {attempt} failed: {last_error}")
                
                if attempt < retry_count:
                    # Exponential backoff
                    backoff_time = min(2 ** attempt, 10)  # Max 10 seconds
                    log.info(f"Retrying in {backoff_time}s...")
                    time.sleep(backoff_time)
                    continue
                else:
                    # Final attempt failed
                    log.error(f"All {retry_count} attempts failed")
                    return {
                        "error": last_error,
                        "results": [],
                        "query": query,
                        "count": 0
                    }
            
            # Success - log response (truncate large payloads)
            results = response.get("results", [])
            result_count = len(results)
            
            # Truncate result logging for large payloads
            if result_count > 0:
                first_result = results[0]
                title = first_result.get("title", "N/A")[:50]
                log.info(f"Search successful: {result_count} results (first: '{title}...')")
            else:
                log.warning("Search returned no results")
            
            return {
                "results": results,
                "query": query,
                "count": result_count,
                "attempt": attempt
            }
            
        except Exception as e:
            last_error = str(e)
            log.error(f"Attempt {attempt} exception: {e}")
            
            if attempt < retry_count:
                backoff_time = min(2 ** attempt, 10)
                log.info(f"Retrying in {backoff_time}s...")
                time.sleep(backoff_time)
            else:
                # All retries exhausted
                log.error(f"All {retry_count} attempts failed with exceptions")
                return {
                    "error": f"Failed after {retry_count} attempts: {last_error}",
                    "results": [],
                    "query": query,
                    "count": 0
                }
    
    # Shouldn't reach here, but just in case
    return {
        "error": "Unknown error",
        "results": [],
        "query": query,
        "count": 0
    }


def scrape_url(url: str, retry_count: int = 2) -> Dict[str, Any]:
    """
    Scrape content from a URL with rate limiting and retry
    
    Args:
        url: URL to scrape
        retry_count: Number of retry attempts
        
    Returns:
        Dictionary with content or error
    """
    global _last_request_time
    
    # Rate limiting
    current_time = time.time()
    time_since_last = current_time - _last_request_time
    
    if time_since_last < _min_delay_seconds:
        sleep_time = _min_delay_seconds - time_since_last
        time.sleep(sleep_time)
    
    _last_request_time = time.time()
    
    # Log request (truncate long URLs)
    url_display = url[:80] + "..." if len(url) > 80 else url
    log.info(f"Scrape request: {url_display}")
    
    try:
        from modules.cursor_bridge.client import get_cursor_bridge_client
        client = get_cursor_bridge_client()
    except ImportError as e:
        log.error(f"Failed to import Cursor bridge client: {e}")
        return {"error": str(e), "content": ""}
    
    # Retry loop
    for attempt in range(1, retry_count + 1):
        try:
            response = client.scrape_url(url)
            
            if "error" in response:
                log.warning(f"Scrape attempt {attempt} failed: {response['error']}")
                if attempt < retry_count:
                    time.sleep(2 ** attempt)
                    continue
            
            content_len = len(response.get("content", ""))
            log.info(f"Scrape successful: {content_len} chars")
            
            return response
            
        except Exception as e:
            log.error(f"Scrape attempt {attempt} exception: {e}")
            if attempt < retry_count:
                time.sleep(2 ** attempt)
    
    return {"error": "Scrape failed after retries", "content": ""}

