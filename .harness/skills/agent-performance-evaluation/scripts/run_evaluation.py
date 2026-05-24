#!/usr/bin/env python3
"""
Agent Performance Evaluation Script

This script runs a comprehensive performance test on the financial news agent
and generates a detailed performance report.

Usage:
    python run_evaluation.py
"""

import sys
import json
import os
import glob
from datetime import datetime
from pathlib import Path

# Add agent to path
AGENT_PATH = '/Users/mac/code/agent/financial-news-agent-2'
sys.path.insert(0, AGENT_PATH)

from financial_news_agent.agent import run_agent_with_retry, create_conversation

# Test queries
TEST_QUERIES = [
    {
        "id": 1,
        "category": "simple",
        "query": "What's the latest news about Apple?",
        "expected_characteristics": "Should find recent Apple news, cite sources, provide brief summary"
    },
    {
        "id": 2,
        "category": "simple",
        "query": "What's happening in the semiconductor industry?",
        "expected_characteristics": "Should cover multiple companies, identify trends, cite industry news"
    },
    {
        "id": 3,
        "category": "complex",
        "query": "Compare Tesla and Rivian's recent developments and their competitive positioning",
        "expected_characteristics": "Should find news about both companies, compare them, analyze competitive dynamics"
    },
    {
        "id": 4,
        "category": "complex",
        "query": "What are the major trends in AI chip development? Which companies are leading?",
        "expected_characteristics": "Should identify trends, name key players, provide analysis with sources"
    },
    {
        "id": 5,
        "category": "edge_case",
        "query": "What's the news about NVDA?",
        "expected_characteristics": "Should resolve ticker to Nvidia, find relevant news"
    },
    {
        "id": 6,
        "category": "edge_case",
        "query": "Tell me about Meta's recent announcements",
        "expected_characteristics": "Should correctly identify Meta Platforms (not metaphorical usage), find company news"
    }
]


def generate_report(results: list, run_dir: str, timestamp: str) -> str:
    """Generate a comprehensive performance report."""

    report = []
    report.append("# Agent Performance Evaluation Report")
    report.append(f"\n**Run Date**: {timestamp}")
    report.append(f"**Test Cases**: {len(results)}")
    report.append(f"**Run Directory**: {run_dir}\n")

    # Overall Statistics
    report.append("## Overall Statistics\n")

    avg_accuracy = sum(r['accuracy'] for r in results) / len(results)
    avg_relevance = sum(r['relevance'] for r in results) / len(results)
    avg_coherence = sum(r['coherence'] for r in results) / len(results)
    avg_reasonableness = sum(r['reasonableness'] for r in results) / len(results)
    avg_overall = sum(r['overall_score'] for r in results) / len(results)

    report.append(f"- **Average Overall Score**: {avg_overall:.2f}/10")
    report.append(f"- **Average Accuracy**: {avg_accuracy:.2f}/10")
    report.append(f"- **Average Relevance**: {avg_relevance:.2f}/10")
    report.append(f"- **Average Coherence**: {avg_coherence:.2f}/10")
    report.append(f"- **Average Reasonableness**: {avg_reasonableness:.2f}/10")

    total_retries = sum(r['retry_count'] for r in results)
    retry_rate = (sum(1 for r in results if r['retry_triggered']) / len(results)) * 100

    report.append(f"- **Total Retries**: {total_retries}")
    report.append(f"- **Retry Rate**: {retry_rate:.1f}%")

    avg_duration = sum(r['total_duration_ms'] for r in results) / len(results)
    avg_sources = sum(r['source_count'] for r in results) / len(results)

    report.append(f"- **Average Duration**: {avg_duration:.0f}ms ({avg_duration/1000:.1f}s)")
    report.append(f"- **Average Sources per Query**: {avg_sources:.1f}")

    # Detailed Results Table
    report.append("\n## Detailed Results\n")
    report.append("| ID | Category | Query | Overall | Acc | Rel | Coh | Rea | Sources | Time(s) | Retry |")
    report.append("|----|----------|-------|---------|-----|-----|-----|-----|---------|---------|-------|")

    for r in results:
        query_short = r['query'][:40] + "..." if len(r['query']) > 40 else r['query']
        retry_mark = "✓" if r['retry_triggered'] else ""
        report.append(
            f"| {r['test_id']} | {r['category']} | {query_short} | "
            f"{r['overall_score']:.1f} | {r['accuracy']} | {r['relevance']} | "
            f"{r['coherence']} | {r['reasonableness']} | {r['source_count']} | "
            f"{r['total_duration_ms']/1000:.1f} | {retry_mark} |"
        )

    # Performance by Category
    report.append("\n## Performance by Category\n")

    categories = {}
    for r in results:
        cat = r['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)

    for cat, cat_results in categories.items():
        avg_score = sum(r['overall_score'] for r in cat_results) / len(cat_results)
        avg_time = sum(r['total_duration_ms'] for r in cat_results) / len(cat_results)
        report.append(f"### {cat.replace('_', ' ').title()}")
        report.append(f"- **Average Score**: {avg_score:.2f}/10")
        report.append(f"- **Average Time**: {avg_time/1000:.1f}s")
        report.append(f"- **Test Cases**: {len(cat_results)}\n")

    # Timing Breakdown
    report.append("## Timing Breakdown\n")

    total_time = sum(r['total_duration_ms'] for r in results)
    total_llm = sum(r['llm_time_ms'] for r in results)
    total_api = sum(r['api_time_ms'] for r in results)

    if total_time > 0:
        report.append(f"- **Total Execution Time**: {total_time/1000:.1f}s")
        report.append(f"- **LLM Time**: {total_llm/1000:.1f}s ({(total_llm/total_time*100):.1f}%)")
        report.append(f"- **API Time**: {total_api/1000:.1f}s ({(total_api/total_time*100):.1f}%)")

    # Quality Insights
    report.append("\n## Quality Insights\n")

    low_scores = [r for r in results if r['overall_score'] < 6.0]
    if low_scores:
        report.append(f"⚠️ **{len(low_scores)} test case(s) scored below 6.0:**")
        for r in low_scores:
            report.append(f"- Test {r['test_id']}: {r['query'][:60]}... (Score: {r['overall_score']:.1f})")
    else:
        report.append("✓ All test cases scored 6.0 or above")

    high_performers = [r for r in results if r['overall_score'] >= 8.0]
    if high_performers:
        report.append(f"\n✓ **{len(high_performers)} test case(s) scored 8.0 or above**")

    # Historical Comparison
    eval_dir = Path(run_dir).parent
    previous_runs = sorted(glob.glob(str(eval_dir / 'run-*/results.json')))

    if len(previous_runs) > 1:
        try:
            with open(previous_runs[-2], 'r') as f:
                previous_results = json.load(f)

            prev_avg = sum(r['overall_score'] for r in previous_results) / len(previous_results)
            curr_avg = avg_overall

            delta = curr_avg - prev_avg
            direction = "↑" if delta > 0 else "↓" if delta < 0 else "→"

            report.append("\n## Historical Comparison\n")
            report.append(f"- **Previous run average**: {prev_avg:.2f}/10")
            report.append(f"- **Current run average**: {curr_avg:.2f}/10")
            report.append(f"- **Change**: {direction} {abs(delta):.2f} points")
        except Exception as e:
            report.append(f"\n## Historical Comparison\n")
            report.append(f"Could not load previous run: {e}")

    return "\n".join(report)


def run_evaluation() -> dict:
    """Run the evaluation and generate report."""

    # Setup output directory
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    output_dir = Path(AGENT_PATH) / '.harness' / 'eval' / f'run-{timestamp}'
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {output_dir}")
    print(f"Running {len(TEST_QUERIES)} test queries...\n")

    results = []

    for test_case in TEST_QUERIES:
        print(f"{'='*60}")
        print(f"Test {test_case['id']}/{len(TEST_QUERIES)}: {test_case['query'][:50]}...")
        print(f"{'='*60}")

        try:
            # Execute the agent with fresh conversation
            messages = create_conversation()
            result, updated_messages = run_agent_with_retry(test_case['query'], messages)

            # Extract metrics
            metrics = {
                'test_id': test_case['id'],
                'category': test_case['category'],
                'query': test_case['query'],
                'timestamp': datetime.now().isoformat(),

                # Evaluation scores
                'accuracy': result['evaluation']['accuracy'],
                'relevance': result['evaluation']['relevance'],
                'coherence': result['evaluation']['coherence'],
                'reasonableness': result['evaluation']['reasonableness'],
                'overall_score': result['evaluation']['overall'],

                # Execution metrics
                'source_count': len(result['sources']),
                'tool_call_count': len(result['tool_calls']),
                'reasoning_steps': len(result['reasoning_steps']),

                # Timing data (if available)
                'total_duration_ms': result['trace'].get('timing', {}).get('total_duration_ms', 0),
                'llm_time_ms': result['trace'].get('timing', {}).get('breakdown', {}).get('llm_call', {}).get('total_ms', 0),
                'api_time_ms': result['trace'].get('timing', {}).get('breakdown', {}).get('api_call', {}).get('total_ms', 0),

                # Retry information
                'retry_count': len(result.get('retry_history', [])),
                'retry_triggered': len(result.get('retry_history', [])) > 0,

                # Full result for detailed analysis
                'full_result': result
            }

            results.append(metrics)

            print(f"✓ Completed - Score: {metrics['overall_score']:.1f}/10\n")

        except Exception as e:
            print(f"✗ Failed: {str(e)}\n")
            # Continue with other tests even if one fails

    # Save raw results
    results_file = output_dir / 'results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    # Save test queries
    queries_file = output_dir / 'test_queries.json'
    with open(queries_file, 'w') as f:
        json.dump(TEST_QUERIES, f, indent=2)

    print(f"{'='*60}")
    print(f"Completed {len(results)}/{len(TEST_QUERIES)} tests")
    print(f"{'='*60}\n")

    # Generate report
    print("Generating performance report...")
    run_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report_text = generate_report(results, str(output_dir), run_timestamp)

    report_file = output_dir / 'performance_report.md'
    with open(report_file, 'w') as f:
        f.write(report_text)

    print(f"\n{'='*60}")
    print(f"✓ Evaluation complete!")
    print(f"{'='*60}")
    print(f"Results: {results_file}")
    print(f"Report:  {report_file}")
    print(f"{'='*60}\n")

    return {'results': results, 'output_dir': str(output_dir), 'report_file': str(report_file)}


if __name__ == '__main__':
    # Run evaluation and generate report
    result = run_evaluation()

    print("\nTo view the report:")
    print(f"  cat {result['report_file']}")
