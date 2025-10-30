#!/usr/bin/env python
"""
Simple load testing for RAG query endpoint.

Sends concurrent queries and measures latency percentiles.
"""

import sys
import time
import statistics
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

# Sample questions for load testing
SAMPLE_QUESTIONS = [
    "What is RAGGITY ZYZTEM?",
    "How do I start the API server?",
    "What vector stores are supported?",
    "Explain the CLO 3D integration",
    "What LLM providers can I use?",
    "How does the hybrid cloud mode work?",
    "What file formats are supported for ingestion?",
    "How do I configure the system?",
    "What are the main features?",
    "How do I run the UI?",
]


def send_query(question: str, base_url: str = "http://localhost:8000") -> Tuple[bool, float, str]:
    """
    Send a single query and measure latency.
    
    Returns:
        (success, latency_ms, error_message)
    """
    start = time.perf_counter()
    
    try:
        response = requests.get(
            f"{base_url}/query",
            params={"q": question, "k": 3},
            timeout=30
        )
        
        latency = (time.perf_counter() - start) * 1000  # milliseconds
        
        if response.ok:
            return True, latency, ""
        else:
            return False, latency, f"HTTP {response.status_code}"
    
    except requests.exceptions.Timeout:
        latency = (time.perf_counter() - start) * 1000
        return False, latency, "Timeout"
    
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return False, latency, str(e)


def run_load_test(num_requests: int = 100, concurrency: int = 5, 
                  base_url: str = "http://localhost:8000") -> dict:
    """
    Run load test with concurrent requests.
    
    Args:
        num_requests: Total number of requests to send
        concurrency: Number of concurrent workers
        base_url: API base URL
    
    Returns:
        Dictionary with test results
    """
    print(f"\n{'='*60}")
    print(f"RAG Query Load Test")
    print(f"{'='*60}")
    print(f"Requests: {num_requests}")
    print(f"Concurrency: {concurrency}")
    print(f"Target: {base_url}")
    print(f"{'='*60}\n")
    
    # Prepare questions (cycle through sample questions)
    questions = [SAMPLE_QUESTIONS[i % len(SAMPLE_QUESTIONS)] for i in range(num_requests)]
    
    # Track results
    latencies = []
    successes = 0
    failures = 0
    errors = []
    
    start_time = time.perf_counter()
    
    # Run with thread pool
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        # Submit all tasks
        futures = [executor.submit(send_query, q, base_url) for q in questions]
        
        # Collect results with progress
        completed = 0
        for future in as_completed(futures):
            success, latency, error = future.result()
            
            latencies.append(latency)
            
            if success:
                successes += 1
            else:
                failures += 1
                if error:
                    errors.append(error)
            
            completed += 1
            
            # Progress update every 10 requests
            if completed % 10 == 0 or completed == num_requests:
                print(f"Progress: {completed}/{num_requests} ({completed/num_requests*100:.1f}%)")
    
    total_time = time.perf_counter() - start_time
    
    # Calculate statistics
    latencies.sort()
    
    p50 = statistics.median(latencies) if latencies else 0
    p95 = latencies[int(len(latencies) * 0.95)] if len(latencies) > 0 else 0
    p99 = latencies[int(len(latencies) * 0.99)] if len(latencies) > 0 else 0
    avg = statistics.mean(latencies) if latencies else 0
    min_lat = min(latencies) if latencies else 0
    max_lat = max(latencies) if latencies else 0
    
    requests_per_sec = num_requests / total_time if total_time > 0 else 0
    
    # Print results
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Requests/sec: {requests_per_sec:.2f}")
    print(f"\nSuccess Rate: {successes}/{num_requests} ({successes/num_requests*100:.1f}%)")
    print(f"Failures: {failures}")
    print(f"\nLatency Percentiles (ms):")
    print(f"  Min:  {min_lat:.1f}")
    print(f"  P50:  {p50:.1f}")
    print(f"  P95:  {p95:.1f}")
    print(f"  P99:  {p99:.1f}")
    print(f"  Max:  {max_lat:.1f}")
    print(f"  Avg:  {avg:.1f}")
    
    if errors:
        print(f"\nError Summary:")
        error_counts = {}
        for err in errors:
            error_counts[err] = error_counts.get(err, 0) + 1
        for err, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            print(f"  {err}: {count}")
    
    print(f"{'='*60}\n")
    
    return {
        "num_requests": num_requests,
        "concurrency": concurrency,
        "total_time": round(total_time, 2),
        "requests_per_sec": round(requests_per_sec, 2),
        "successes": successes,
        "failures": failures,
        "latency": {
            "min": round(min_lat, 1),
            "p50": round(p50, 1),
            "p95": round(p95, 1),
            "p99": round(p99, 1),
            "max": round(max_lat, 1),
            "avg": round(avg, 1)
        },
        "errors": errors
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load test RAG query endpoint")
    parser.add_argument(
        "-n", "--num-requests",
        type=int,
        default=100,
        help="Total number of requests (default: 100)"
    )
    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=5,
        help="Number of concurrent workers (default: 5)"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    try:
        results = run_load_test(
            num_requests=args.num_requests,
            concurrency=args.concurrency,
            base_url=args.url
        )
        
        # Exit with error if too many failures
        failure_rate = results['failures'] / results['num_requests']
        if failure_rate > 0.1:  # More than 10% failures
            print(f"⚠️  Warning: High failure rate ({failure_rate*100:.1f}%)")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\nLoad test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running load test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

