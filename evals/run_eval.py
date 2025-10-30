#!/usr/bin/env python
"""
Evaluation Harness for RAG System

Runs question-answer pairs against the RAG engine and computes metrics.
Compares results to best historical scores and saves detailed reports.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from core.rag_engine import RAGEngine
from core.config import CFG
from logger import get_logger

log = get_logger("eval")


def load_eval_set(eval_file: str) -> Dict[str, Any]:
    """Load evaluation set from YAML file"""
    with open(eval_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def exact_match(answer: str, expected: str) -> bool:
    """Check if answer exactly matches expected (case-insensitive)"""
    return answer.strip().lower() == expected.strip().lower()


def substring_match(answer: str, expected: str) -> bool:
    """Check if expected substring appears in answer (case-insensitive)"""
    return expected.strip().lower() in answer.strip().lower()


def keywords_match(answer: str, keywords: List[str]) -> bool:
    """Check if any keyword appears in answer (case-insensitive)"""
    answer_lower = answer.strip().lower()
    return any(kw.lower() in answer_lower for kw in keywords)


def compute_rouge_l(answer: str, expected: str) -> float:
    """
    Compute ROUGE-L score (optional).
    Returns 0 if rouge package not available.
    """
    try:
        from rouge import Rouge
        rouge = Rouge()
        scores = rouge.get_scores(answer, expected)
        return scores[0]['rouge-l']['f']
    except ImportError:
        return 0.0


def evaluate_qa_pair(rag: RAGEngine, qa: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a single QA pair.
    
    Returns:
        Dictionary with evaluation results
    """
    question = qa['question']
    expected = qa['expected_answer']
    match_type = qa.get('match_type', 'substring')
    keywords = qa.get('keywords', [expected])
    
    start_time = time.time()
    
    try:
        result = rag.query(question, k=3)
        answer = result.get('answer', '')
        contexts = result.get('contexts', [])
        latency = (time.time() - start_time) * 1000  # milliseconds
        
        # Compute match based on type
        if match_type == 'exact':
            passed = exact_match(answer, expected)
        elif match_type == 'substring':
            passed = substring_match(answer, expected)
        elif match_type == 'keywords':
            passed = keywords_match(answer, keywords)
        else:
            passed = False
        
        # Optional: Compute ROUGE-L
        rouge_l = compute_rouge_l(answer, expected)
        
        return {
            "question": question,
            "expected": expected,
            "answer": answer,
            "match_type": match_type,
            "passed": passed,
            "latency_ms": round(latency, 2),
            "contexts_count": len(contexts),
            "rouge_l": round(rouge_l, 3) if rouge_l > 0 else None
        }
    
    except Exception as e:
        log.error(f"Error evaluating question '{question}': {e}")
        return {
            "question": question,
            "expected": expected,
            "answer": None,
            "match_type": match_type,
            "passed": False,
            "error": str(e),
            "latency_ms": (time.time() - start_time) * 1000
        }


def run_evaluation(eval_file: str, store_dir: str = None) -> Dict[str, Any]:
    """
    Run full evaluation suite.
    
    Args:
        eval_file: Path to YAML evaluation file
        store_dir: Optional vector store directory
    
    Returns:
        Evaluation results dictionary
    """
    log.info(f"Loading evaluation set: {eval_file}")
    eval_set = load_eval_set(eval_file)
    
    # Initialize RAG engine
    rag = RAGEngine(store_dir=store_dir)
    
    # Ingest documents
    documents = eval_set.get('documents', [])
    for doc in documents:
        doc_path = doc['path']
        log.info(f"Ingesting document: {doc_path}")
        if os.path.exists(doc_path):
            rag.ingest_path(doc_path)
        else:
            log.warning(f"Document not found: {doc_path}")
    
    # Run QA pairs
    qa_pairs = eval_set.get('qa_pairs', [])
    results = []
    
    for qa in qa_pairs:
        log.info(f"Evaluating: {qa['question']}")
        result = evaluate_qa_pair(rag, qa)
        results.append(result)
    
    # Compute metrics
    total = len(results)
    passed = sum(1 for r in results if r.get('passed', False))
    
    # Metrics by match type
    by_type = {}
    for match_type in ['exact', 'substring', 'keywords']:
        type_results = [r for r in results if r.get('match_type') == match_type]
        if type_results:
            type_passed = sum(1 for r in type_results if r.get('passed', False))
            by_type[match_type] = {
                "total": len(type_results),
                "passed": type_passed,
                "score": type_passed / len(type_results) if type_results else 0.0
            }
    
    # Average latency
    latencies = [r['latency_ms'] for r in results if 'latency_ms' in r]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
    # Overall score
    overall_score = passed / total if total > 0 else 0.0
    
    # Check thresholds
    thresholds = eval_set.get('thresholds', {})
    meets_threshold = overall_score >= thresholds.get('min_overall', 0.65)
    
    return {
        "timestamp": time.time(),
        "eval_file": eval_file,
        "total_questions": total,
        "passed": passed,
        "failed": total - passed,
        "overall_score": round(overall_score, 3),
        "by_match_type": by_type,
        "avg_latency_ms": round(avg_latency, 2),
        "meets_threshold": meets_threshold,
        "thresholds": thresholds,
        "results": results
    }


def save_results(results: Dict[str, Any], output_dir: str = "evals/results"):
    """Save evaluation results to JSON file"""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_file = os.path.join(output_dir, f"eval_{timestamp}.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    log.info(f"Results saved to: {output_file}")
    return output_file


def compare_to_best(results: Dict[str, Any], results_dir: str = "evals/results") -> Dict[str, Any]:
    """
    Compare current results to best historical results.
    
    Returns:
        Comparison dictionary
    """
    if not os.path.exists(results_dir):
        return {"is_best": True, "improvement": None}
    
    # Find best previous score
    best_score = 0.0
    best_file = None
    
    for filename in os.listdir(results_dir):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(results_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                past_results = json.load(f)
                past_score = past_results.get('overall_score', 0.0)
                
                if past_score > best_score:
                    best_score = past_score
                    best_file = filename
        except Exception:
            continue
    
    current_score = results['overall_score']
    is_best = current_score >= best_score
    improvement = current_score - best_score if best_score > 0 else None
    
    return {
        "is_best": is_best,
        "current_score": current_score,
        "best_score": best_score,
        "improvement": round(improvement, 3) if improvement is not None else None,
        "best_file": best_file
    }


def print_summary(results: Dict[str, Any], comparison: Dict[str, Any]):
    """Print evaluation summary to console"""
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    print(f"Total Questions: {results['total_questions']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Overall Score: {results['overall_score']:.1%}")
    print(f"Avg Latency: {results['avg_latency_ms']:.1f} ms")
    print()
    
    print("By Match Type:")
    for match_type, metrics in results['by_match_type'].items():
        print(f"  {match_type}: {metrics['passed']}/{metrics['total']} ({metrics['score']:.1%})")
    print()
    
    print("Thresholds:")
    meets = "✓ PASS" if results['meets_threshold'] else "✗ FAIL"
    print(f"  Min Overall: {results['thresholds'].get('min_overall', 0.65):.1%} - {meets}")
    print()
    
    print("Historical Comparison:")
    if comparison['is_best']:
        print("  🏆 NEW BEST SCORE!")
    else:
        print(f"  Best Score: {comparison['best_score']:.1%}")
        print(f"  Improvement: {comparison['improvement']:+.1%}" if comparison['improvement'] else "  (First run)")
    print("="*60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run RAG evaluation")
    parser.add_argument(
        "--eval-file",
        default="evals/sets/demo.yaml",
        help="Path to evaluation YAML file"
    )
    parser.add_argument(
        "--store-dir",
        default=None,
        help="Vector store directory (default: use config)"
    )
    parser.add_argument(
        "--output-dir",
        default="evals/results",
        help="Output directory for results"
    )
    
    args = parser.parse_args()
    
    # Run evaluation
    results = run_evaluation(args.eval_file, args.store_dir)
    
    # Save results
    output_file = save_results(results, args.output_dir)
    
    # Compare to best
    comparison = compare_to_best(results, args.output_dir)
    
    # Print summary
    print_summary(results, comparison)
    
    # Exit with code based on threshold
    sys.exit(0 if results['meets_threshold'] else 1)

