"""
performance_test.py
------------------
Performance & Load Testing Suite.
Measures system behavior under 10, 50, and 100 concurrent/sequential requests.
"""

import time
import json
import statistics
import concurrent.futures
from database.connection import db_manager
from workflow import run_workflow

# Sample enterprise incident queries for load generation
QUERIES = [
    "VPN connection timeout error during TLS handshake",
    "VPN connected but cannot ping internal 10.x IP range",
    "Printer spooler offline documents queued not printing",
    "Outlook status bar shows Disconnected or Need Password",
    "Windows update error 0x80070002",
    "Domain user account locked out",
    "DNS resolution failure for internal host names",
    "Software installer requires admin privileges",
    "Disable user account for EMP1026 due to security breach",
    "Unknown legacy COBOL system database corruption error X99"
]

def run_single_test(query: str, idx: int) -> dict:
    emp_id = f"EMP{1000 + idx}"
    
    # 1. Measure DB connection / query overhead
    db_start = time.monotonic()
    db_manager.fetchone("SELECT 1")
    db_time_ms = (time.monotonic() - db_start) * 1000
    
    # 2. Execute full 5-agent LangGraph workflow
    start_time = time.monotonic()
    success = False
    error = None
    res = {}
    try:
        res = run_workflow(query, employee_id=emp_id)
        success = True
    except Exception as e:
        error = str(e)
        
    total_time_ms = (time.monotonic() - start_time) * 1000
    
    return {
        "success": success,
        "total_time_ms": total_time_ms,
        "db_time_ms": db_time_ms,
        "agent_timings": res.get("timings", {}),
        "error": error
    }

def run_workload_test(size: int, max_workers: int = 10) -> dict:
    print(f"\n[*] Initiating Workload Test: {size} Incidents (Concurrency: {max_workers} Workers)")
    
    # Build incident batch
    tasks = []
    for i in range(size):
        query = QUERIES[i % len(QUERIES)]
        tasks.append((query, i))
        
    start_time = time.monotonic()
    results = []
    
    # Execute batch concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_single_test, q, idx): (q, idx) for q, idx in tasks}
        for fut in concurrent.futures.as_completed(futures):
            results.append(fut.result())
            
    total_elapsed_sec = time.monotonic() - start_time
    
    # Compile performance metrics
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    failure_rate = (len(failures) / size) * 100
    
    latencies = [r["total_time_ms"] for r in successes]
    db_times = [r["db_time_ms"] for r in results]
    
    avg_latency = statistics.mean(latencies) if latencies else 0.0
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (max(latencies) if latencies else 0.0)
    avg_db_time = statistics.mean(db_times) if db_times else 0.0
    
    # Aggregate agent node averages
    agent_averages = {}
    for agent_name in ["planner", "researcher", "analysis", "decision", "auto_fix", "escalate", "executor"]:
        agent_times = [r["agent_timings"].get(agent_name, 0.0) * 1000 for r in successes if agent_name in r["agent_timings"]]
        agent_averages[agent_name] = statistics.mean(agent_times) if agent_times else 0.0
        
    print(f"[-] Workload completed in: {total_elapsed_sec:.2f} seconds")
    print(f"[-] Throughput: {size / total_elapsed_sec:.2f} incidents/sec")
    print(f"[-] Success Rate: {len(successes)}/{size} ({100 - failure_rate:.1f}%)")
    print(f"[-] Avg Workflow Latency: {avg_latency:.1f} ms (p95: {p95_latency:.1f} ms)")
    print(f"[-] Avg DB Execution Time: {avg_db_time:.2f} ms")
    
    return {
        "workload_size": size,
        "total_elapsed_sec": total_elapsed_sec,
        "throughput_req_sec": size / total_elapsed_sec,
        "success_rate": 100 - failure_rate,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
        "avg_db_time_ms": avg_db_time,
        "agent_averages_ms": agent_averages
    }

if __name__ == "__main__":
    from database.init_db import init_databases
    init_databases()
    
    print("\n==================================================")
    print(" AI Coordination Platform Performance load Suite")
    print("==================================================")
    
    summary_metrics = []
    # Test workloads
    for size in [10, 50, 100]:
        res = run_workload_test(size, max_workers=10)
        summary_metrics.append(res)
        
    print("\n" + "=" * 32 + " SUMMARY REPORT " + "=" * 32)
    print(f"{'Workload':<10} | {'Throughput':<14} | {'Avg Latency':<12} | {'p95 Latency':<12} | {'DB Latency':<10} | {'Success %':<10}")
    print("-" * 80)
    for s in summary_metrics:
        print(f"{s['workload_size']:<10} | {s['throughput_req_sec']:<10.2f}/sec | {s['avg_latency_ms']:<10.1f}ms | {s['p95_latency_ms']:<10.1f}ms | {s['avg_db_time_ms']:<8.2f}ms | {s['success_rate']:<9.1f}%")
    print("=" * 80 + "\n")
