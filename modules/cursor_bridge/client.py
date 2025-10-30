"""
Cursor Bridge HTTP Client
Provides a simple interface for web retrieval via Cursor browser/proxy
"""

import os
import requests
from typing import Dict, Any, Optional
from logger import get_logger

log = get_logger("cursor_bridge_client")


class CursorBridgeClient:
    """HTTP client for Cursor bridge endpoints"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Cursor bridge client
        
        Args:
            base_url: Base URL for Cursor bridge. Defaults to env var or localhost.
        """
        self.base_url = base_url or os.getenv(
            "CURSOR_BRIDGE_URL",
            "http://localhost:8080"
        )
        self.timeout = int(os.getenv("CURSOR_BRIDGE_TIMEOUT", "30"))
        
        log.info(f"CursorBridgeClient initialized with base_url: {self.base_url}")
    
    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Perform web search via Cursor bridge
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with search results or error
        """
        try:
            endpoint = f"{self.base_url}/api/search"
            
            payload = {
                "query": query,
                "max_results": max_results
            }
            
            log.info(f"Sending search request: {query[:100]}...")
            
            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            log.info(f"Search successful, got {len(data.get('results', []))} results")
            return data
            
        except requests.exceptions.Timeout:
            log.error(f"Search timeout after {self.timeout}s")
            return {
                "error": "Request timeout",
                "results": []
            }
        except requests.exceptions.ConnectionError:
            log.error(f"Connection error to {self.base_url}")
            return {
                "error": "Connection failed - is Cursor bridge running?",
                "results": []
            }
        except requests.exceptions.HTTPError as e:
            log.error(f"HTTP error: {e.response.status_code}")
            return {
                "error": f"HTTP {e.response.status_code}",
                "results": []
            }
        except Exception as e:
            log.error(f"Unexpected error in search: {e}")
            return {
                "error": str(e),
                "results": []
            }
    
    def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a URL via Cursor bridge
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with scraped content or error
        """
        try:
            endpoint = f"{self.base_url}/api/scrape"
            
            payload = {"url": url}
            
            log.info(f"Scraping URL: {url}")
            
            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            content_length = len(data.get("content", ""))
            log.info(f"Scrape successful, got {content_length} chars")
            
            return data
            
        except Exception as e:
            log.error(f"Error scraping URL: {e}")
            return {
                "error": str(e),
                "content": ""
            }
    
    def health_check(self) -> bool:
        """
        Check if Cursor bridge is healthy
        
        Returns:
            True if bridge is responding, False otherwise
        """
        try:
            endpoint = f"{self.base_url}/health"
            response = requests.get(endpoint, timeout=5)
            
            if response.status_code == 200:
                log.info("Cursor bridge health check passed")
                return True
            else:
                log.warning(f"Cursor bridge unhealthy: {response.status_code}")
                return False
                
        except Exception as e:
            log.error(f"Cursor bridge health check failed: {e}")
            return False


# Global client instance
_client = None


def get_cursor_bridge_client() -> CursorBridgeClient:
    """Get global Cursor bridge client instance"""
    global _client
    if _client is None:
        _client = CursorBridgeClient()
    return _client

