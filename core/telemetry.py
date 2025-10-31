"""
Telemetry and structured event logging.

Provides structured JSON event logging and optional Prometheus metrics
for monitoring system performance and usage.
"""

import json
import time
import os
import sys
from typing import Any, Dict
from collections import defaultdict
import threading

from .config import CFG

# Add parent directory to path to import logger
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import get_logger

log = get_logger("telemetry")

# Metrics storage (thread-safe)
_metrics_lock = threading.Lock()
_metrics = {
    "ingests_total": 0,
    "ingests_chunks_total": 0,
    "queries_total": 0,
    "errors_total": 0,
    "errors_by_type": defaultdict(int),
}


def event(name: str, **kwargs):
    """
    Log a structured JSON event.
    
    Args:
        name: Event name (e.g., "ingest.start", "query.complete")
        **kwargs: Additional event data
    
    Usage:
        event("ingest.start", path="/docs", file_count=5)
        event("query", latency_ms=123.4, contexts=3)
    """
    payload = {
        "ts": time.time(),
        "name": name,
        **kwargs
    }
    
    # Add environment if available
    if hasattr(CFG, 'env'):
        payload["env"] = CFG.env
    
    log.info("[EVENT] " + json.dumps(payload))
    
    # Update metrics based on event type
    _update_metrics(name, kwargs)


def _update_metrics(event_name: str, data: Dict[str, Any]):
    """Update Prometheus-style metrics based on events"""
    with _metrics_lock:
        if event_name == "ingest.complete":
            _metrics["ingests_total"] += 1
            chunks = data.get("chunks", 0)
            _metrics["ingests_chunks_total"] += chunks
        
        elif event_name == "query.complete":
            _metrics["queries_total"] += 1
        
        elif event_name.startswith("error."):
            _metrics["errors_total"] += 1
            error_type = data.get("type", "unknown")
            _metrics["errors_by_type"][error_type] += 1


def get_metrics() -> Dict[str, Any]:
    """
    Get current metrics snapshot.
    
    Returns:
        Dictionary of metrics
    """
    with _metrics_lock:
        return {
            "ingests_total": _metrics["ingests_total"],
            "ingests_chunks_total": _metrics["ingests_chunks_total"],
            "queries_total": _metrics["queries_total"],
            "errors_total": _metrics["errors_total"],
            "errors_by_type": dict(_metrics["errors_by_type"]),
        }


def prometheus_format() -> str:
    """
    Export metrics in Prometheus text format.
    
    Returns:
        Prometheus-formatted metrics string
    """
    metrics = get_metrics()
    
    lines = [
        "# HELP raggity_ingests_total Total number of document ingestion operations",
        "# TYPE raggity_ingests_total counter",
        f"raggity_ingests_total {metrics['ingests_total']}",
        "",
        "# HELP raggity_ingests_chunks_total Total number of chunks ingested",
        "# TYPE raggity_ingests_chunks_total counter",
        f"raggity_ingests_chunks_total {metrics['ingests_chunks_total']}",
        "",
        "# HELP raggity_queries_total Total number of queries processed",
        "# TYPE raggity_queries_total counter",
        f"raggity_queries_total {metrics['queries_total']}",
        "",
        "# HELP raggity_errors_total Total number of errors",
        "# TYPE raggity_errors_total counter",
        f"raggity_errors_total {metrics['errors_total']}",
        "",
    ]
    
    # Add errors by type
    if metrics['errors_by_type']:
        lines.extend([
            "# HELP raggity_errors_by_type Errors grouped by type",
            "# TYPE raggity_errors_by_type counter",
        ])
        for error_type, count in metrics['errors_by_type'].items():
            lines.append(f'raggity_errors_by_type{{type="{error_type}"}} {count}')
        lines.append("")
    
    return "\n".join(lines)


def reset_metrics():
    """Reset all metrics to zero (useful for testing)"""
    with _metrics_lock:
        _metrics["ingests_total"] = 0
        _metrics["ingests_chunks_total"] = 0
        _metrics["queries_total"] = 0
        _metrics["errors_total"] = 0
        _metrics["errors_by_type"].clear()

