#!/usr/bin/env python3
"""
Benchmark Tool for CS496 Week 3: Quorum vs Gossip Performance Comparison

This tool measures response times and throughput for both consistency modes.
Run your cluster first, then execute this script to collect performance data.

Usage:
    # Start Quorum mode cluster first
    docker compose up --build
    
    # In another terminal, run benchmark
    python3 benchmark_tool.py --mode quorum
    
    # Stop cluster, start Gossip mode
    docker compose down
    docker compose -f docker-compose.eventual.yml up --build
    
    # Run benchmark for Gossip
    python3 benchmark_tool.py --mode gossip
    
    # Or run a quick comparison (requires manual cluster restart between modes)
    python3 benchmark_tool.py --compare
"""

import argparse
import json
import requests
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Default configuration
DEFAULT_BASE_URLS = [
    "http://localhost:5001",
    "http://localhost:5002", 
    "http://localhost:5003"
]
DEFAULT_ITERATIONS = 10
DEFAULT_CONCURRENT_REQUESTS = 5
REQUEST_TIMEOUT = 10


def measure_single_post(base_url: str, message_id: int) -> dict:
    """Send a single POST request and measure response time."""
    payload = {
        "text": f"benchmark_message_{message_id}_{int(time.time() * 1000)}",
        "user": "benchmark_tool"
    }
    
    start_time = time.perf_counter()
    try:
        response = requests.post(
            f"{base_url}/message",
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return {
            "success": True,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "message_id": message_id
        }
    except requests.exceptions.Timeout:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return {
            "success": False,
            "status_code": None,
            "elapsed_ms": elapsed_ms,
            "error": "timeout",
            "message_id": message_id
        }
    except requests.exceptions.ConnectionError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return {
            "success": False,
            "status_code": None,
            "elapsed_ms": elapsed_ms,
            "error": str(e),
            "message_id": message_id
        }


def measure_get_messages(base_url: str) -> dict:
    """Measure GET /messages response time."""
    start_time = time.perf_counter()
    try:
        response = requests.get(f"{base_url}/messages", timeout=REQUEST_TIMEOUT)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        if response.status_code == 200:
            data = response.json()
            # Handle both {"messages": [...]} and direct list formats
            if isinstance(data, dict):
                message_count = data.get("count", len(data.get("messages", [])))
            else:
                message_count = len(data)
        else:
            message_count = 0
        return {
            "success": True,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "message_count": message_count
        }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return {
            "success": False,
            "elapsed_ms": elapsed_ms,
            "error": str(e)
        }


def run_sequential_benchmark(base_url: str, iterations: int) -> list:
    """Run sequential POST requests and collect timing data."""
    results = []
    print(f"  Running {iterations} sequential POST requests to {base_url}...")
    
    for i in range(iterations):
        result = measure_single_post(base_url, i)
        results.append(result)
        status = "OK" if result["success"] else "FAIL"
        print(f"    [{i+1}/{iterations}] {result['elapsed_ms']:.2f}ms - {status}")
    
    return results


def run_concurrent_benchmark(base_url: str, num_requests: int) -> list:
    """Run concurrent POST requests and collect timing data."""
    results = []
    print(f"  Running {num_requests} concurrent POST requests to {base_url}...")
    
    start_time = time.perf_counter()
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [
            executor.submit(measure_single_post, base_url, i) 
            for i in range(num_requests)
        ]
        for future in as_completed(futures):
            results.append(future.result())
    
    total_time = (time.perf_counter() - start_time) * 1000
    print(f"    Total time for {num_requests} concurrent requests: {total_time:.2f}ms")
    
    return results


def run_convergence_test(base_urls: list) -> dict:
    """Test how long it takes for a message to appear on all nodes."""
    print("  Running convergence test...")
    
    # Send message to first node
    unique_text = f"convergence_test_{int(time.time() * 1000)}"
    payload = {"text": unique_text, "user": "benchmark_tool"}
    
    start_time = time.perf_counter()
    response = requests.post(f"{base_urls[0]}/message", json=payload, timeout=REQUEST_TIMEOUT)
    post_time = (time.perf_counter() - start_time) * 1000
    
    if response.status_code not in [200, 202]:
        return {"success": False, "error": f"POST failed with {response.status_code}"}
    
    # Check when message appears on other nodes
    convergence_times = {}
    max_wait = 30  # seconds
    check_interval = 0.5  # seconds
    
    for node_url in base_urls[1:]:
        node_start = time.perf_counter()
        found = False
        
        while (time.perf_counter() - start_time) < max_wait:
            try:
                resp = requests.get(f"{node_url}/messages", timeout=REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    data = resp.json()
                    # Handle both {"messages": [...]} and direct list formats
                    messages = data.get("messages", []) if isinstance(data, dict) else data
                    if any(m.get("text") == unique_text for m in messages):
                        convergence_times[node_url] = (time.perf_counter() - start_time) * 1000
                        found = True
                        break
            except Exception:
                pass
            time.sleep(check_interval)
        
        if not found:
            convergence_times[node_url] = None  # Did not converge within timeout
    
    return {
        "success": True,
        "post_time_ms": post_time,
        "convergence_times_ms": convergence_times,
        "all_converged": all(t is not None for t in convergence_times.values())
    }


def calculate_statistics(results: list) -> dict:
    """Calculate statistics from benchmark results."""
    successful = [r for r in results if r.get("success")]
    times = [r["elapsed_ms"] for r in successful]
    
    if not times:
        return {"error": "No successful requests"}
    
    return {
        "count": len(results),
        "successful": len(successful),
        "failed": len(results) - len(successful),
        "min_ms": min(times),
        "max_ms": max(times),
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "p95_ms": sorted(times)[int(len(times) * 0.95)] if len(times) >= 20 else max(times)
    }


def print_statistics(stats: dict, label: str):
    """Print formatted statistics."""
    print(f"\n  {label}:")
    print(f"    Requests: {stats['successful']}/{stats['count']} successful")
    print(f"    Min:      {stats['min_ms']:.2f} ms")
    print(f"    Max:      {stats['max_ms']:.2f} ms")
    print(f"    Mean:     {stats['mean_ms']:.2f} ms")
    print(f"    Median:   {stats['median_ms']:.2f} ms")
    print(f"    Std Dev:  {stats['stdev_ms']:.2f} ms")


def print_analysis_table(mode: str, sequential_stats: dict, concurrent_stats: dict, convergence: dict):
    """Print results in ANALYSIS.md table format."""
    print("\n" + "="*60)
    print("COPY THE FOLLOWING INTO YOUR ANALYSIS.md:")
    print("="*60)
    
    mode_label = "Quorum Mode (Strong Consistency)" if mode == "quorum" else "Gossip Mode (Eventual Consistency)"
    
    print(f"\n### {mode_label}")
    print("| Test | Response Time (ms) | Status Code |")
    print("|------|-------------------|-------------|")
    print(f"| Single message POST | {sequential_stats['mean_ms']:.2f} | {'200' if mode == 'quorum' else '202'} |")
    print(f"| GET /messages | [measure manually] | 200 |")
    print(f"| 5 concurrent POSTs (avg) | {concurrent_stats['mean_ms']:.2f} | {'200' if mode == 'quorum' else '202'} |")
    
    if convergence and convergence.get("success"):
        if mode == "gossip":
            conv_times = [t for t in convergence["convergence_times_ms"].values() if t is not None]
            if conv_times:
                print(f"\n**Convergence Time:** {max(conv_times):.2f} ms for all nodes")
            else:
                print(f"\n**Convergence Time:** Did not converge within timeout")
        else:
            print(f"\n**Convergence Time:** Immediate (synchronous replication)")
    
    print("\n" + "="*60)


def check_cluster_health(base_urls: list) -> bool:
    """Check if the cluster is running and accessible."""
    print("Checking cluster health...")
    all_healthy = True
    
    for url in base_urls:
        try:
            response = requests.get(f"{url}/messages", timeout=5)
            if response.status_code == 200:
                print(f"  {url}: OK")
            else:
                print(f"  {url}: ERROR (status {response.status_code})")
                all_healthy = False
        except requests.exceptions.ConnectionError:
            print(f"  {url}: NOT REACHABLE")
            all_healthy = False
        except Exception as e:
            print(f"  {url}: ERROR ({e})")
            all_healthy = False
    
    return all_healthy


def run_benchmark(mode: str, base_urls: list, iterations: int, concurrent: int):
    """Run the full benchmark suite."""
    print(f"\n{'='*60}")
    print(f"BENCHMARK: {mode.upper()} MODE")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")
    
    if not check_cluster_health(base_urls):
        print("\nERROR: Cluster is not healthy. Please start your cluster first:")
        if mode == "quorum":
            print("  docker compose up --build")
        else:
            print("  docker compose -f docker-compose.eventual.yml up --build")
        sys.exit(1)
    
    primary_url = base_urls[0]
    
    # Sequential benchmark
    print(f"\n[1/3] Sequential POST Benchmark")
    sequential_results = run_sequential_benchmark(primary_url, iterations)
    sequential_stats = calculate_statistics(sequential_results)
    print_statistics(sequential_stats, "Sequential Results")
    
    # Concurrent benchmark
    print(f"\n[2/3] Concurrent POST Benchmark")
    concurrent_results = run_concurrent_benchmark(primary_url, concurrent)
    concurrent_stats = calculate_statistics(concurrent_results)
    print_statistics(concurrent_stats, "Concurrent Results")
    
    # Convergence test
    print(f"\n[3/3] Convergence Test")
    convergence = run_convergence_test(base_urls)
    if convergence.get("success"):
        print(f"    POST response time: {convergence['post_time_ms']:.2f} ms")
        for node, conv_time in convergence["convergence_times_ms"].items():
            if conv_time is not None:
                print(f"    {node}: converged in {conv_time:.2f} ms")
            else:
                print(f"    {node}: did not converge within timeout")
    else:
        print(f"    ERROR: {convergence.get('error')}")
    
    # Print ANALYSIS.md formatted output
    print_analysis_table(mode, sequential_stats, concurrent_stats, convergence)
    
    return {
        "mode": mode,
        "sequential": sequential_stats,
        "concurrent": concurrent_stats,
        "convergence": convergence
    }


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark tool for Quorum vs Gossip performance comparison"
    )
    parser.add_argument(
        "--mode", 
        choices=["quorum", "gossip"],
        required=True,
        help="Consistency mode to benchmark (must match running cluster)"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"Number of sequential requests (default: {DEFAULT_ITERATIONS})"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=DEFAULT_CONCURRENT_REQUESTS,
        help=f"Number of concurrent requests (default: {DEFAULT_CONCURRENT_REQUESTS})"
    )
    parser.add_argument(
        "--urls",
        nargs="+",
        default=DEFAULT_BASE_URLS,
        help="Base URLs of cluster nodes"
    )
    
    args = parser.parse_args()
    
    run_benchmark(args.mode, args.urls, args.iterations, args.concurrent)


if __name__ == "__main__":
    main()
