"""
Golden tests for RAG evaluation.

Ensures that evaluation scores meet minimum thresholds after changes.
This prevents regressions in RAG quality.
"""

import os
import sys
import pytest
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evals.run_eval import run_evaluation


def test_demo_eval_meets_threshold():
    """
    Test that demo evaluation meets minimum quality threshold.
    
    This is a golden test that ensures RAG quality doesn't regress.
    If this test fails, it means changes have degraded RAG performance.
    """
    eval_file = "evals/sets/demo.yaml"
    
    # Skip if eval file doesn't exist (CI environment)
    if not os.path.exists(eval_file):
        pytest.skip(f"Evaluation file not found: {eval_file}")
    
    # Skip if sample doc doesn't exist
    if not os.path.exists("evals/docs/sample.txt"):
        pytest.skip("Sample document not found: evals/docs/sample.txt")
    
    # Run evaluation
    results = run_evaluation(eval_file, store_dir="evals/.test_vector_store")
    
    # Check overall threshold
    assert results['meets_threshold'], (
        f"Evaluation failed to meet threshold. "
        f"Score: {results['overall_score']:.1%}, "
        f"Required: {results['thresholds'].get('min_overall', 0.65):.1%}. "
        f"Passed: {results['passed']}/{results['total_questions']}"
    )
    
    # Additional assertions for specific match types
    by_type = results.get('by_match_type', {})
    
    if 'substring' in by_type:
        substring_score = by_type['substring']['score']
        min_substring = results['thresholds'].get('min_substring_match', 0.6)
        assert substring_score >= min_substring, (
            f"Substring match score {substring_score:.1%} "
            f"below threshold {min_substring:.1%}"
        )
    
    if 'keywords' in by_type:
        keywords_score = by_type['keywords']['score']
        min_keywords = results['thresholds'].get('min_keywords_match', 0.75)
        assert keywords_score >= min_keywords, (
            f"Keywords match score {keywords_score:.1%} "
            f"below threshold {min_keywords:.1%}"
        )


def test_eval_produces_valid_results():
    """Test that evaluation produces valid result structure"""
    eval_file = "evals/sets/demo.yaml"
    
    if not os.path.exists(eval_file):
        pytest.skip(f"Evaluation file not found: {eval_file}")
    
    if not os.path.exists("evals/docs/sample.txt"):
        pytest.skip("Sample document not found")
    
    results = run_evaluation(eval_file, store_dir="evals/.test_vector_store")
    
    # Check required fields
    assert 'overall_score' in results
    assert 'total_questions' in results
    assert 'passed' in results
    assert 'failed' in results
    assert 'results' in results
    
    # Check score is valid
    assert 0.0 <= results['overall_score'] <= 1.0
    
    # Check counts are consistent
    assert results['total_questions'] == results['passed'] + results['failed']
    assert results['total_questions'] == len(results['results'])


def test_individual_qa_results_have_required_fields():
    """Test that individual QA results have all required fields"""
    eval_file = "evals/sets/demo.yaml"
    
    if not os.path.exists(eval_file) or not os.path.exists("evals/docs/sample.txt"):
        pytest.skip("Eval files not found")
    
    results = run_evaluation(eval_file, store_dir="evals/.test_vector_store")
    
    for qa_result in results['results']:
        assert 'question' in qa_result
        assert 'expected' in qa_result
        assert 'match_type' in qa_result
        assert 'passed' in qa_result
        
        # If no error, should have answer and latency
        if 'error' not in qa_result:
            assert 'answer' in qa_result
            assert 'latency_ms' in qa_result

