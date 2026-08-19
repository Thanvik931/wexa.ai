import os
import time
import json
import random
import threading
import concurrent.futures
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

uri = os.getenv("COGNODB_URI")
user = os.getenv("COGNODB_USER")
password = os.getenv("COGNODB_PASSWORD")

CONCURRENCY_LEVELS = [1, 10, 40]
DURATION_PER_SWEEP_SEC = 10
READ_RATIO = 0.80

base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(base_dir, ".."))
nodes_csv = os.path.join(project_root, "data", "nodes.csv")
results_dir = os.path.join(project_root, "harness", "results")
metrics_json = os.path.join(results_dir, "cognodb_mixed.json")

def get_driver(uri_str, auth_tuple):
    return GraphDatabase.driver(uri_str, auth=auth_tuple)

def load_node_ids(csv_path):
    df = pd.read_csv(csv_path)
    return df["id"].tolist()

def execute_worker_operation(driver, node_pool, write_counter_ref):
    op_type = "read" if random.random() < READ_RATIO else "write"
    t0 = time.perf_counter()
    
    with driver.session() as session:
        if op_type == "read":
            start_id = random.choice(node_pool)
            cypher = "MATCH (u:User {id: $start_id})-[r:FRIEND_OF]->(f:User) RETURN count(f) AS out_degree"
            session.run(cypher, {"start_id": int(start_id)}).consume()
        else:
            with write_counter_ref["lock"]:
                write_counter_ref["val"] += 1
                new_id = 9000000 + write_counter_ref["val"]
            cypher = "CREATE (u:User {id: $new_id, label: 'User'})"
            session.run(cypher, {"new_id": int(new_id)}).consume()
            
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return op_type, elapsed_ms

def run_concurrency_sweep(driver, node_pool, num_workers):
    print(f"\n--- Running Mixed Workload Sweep ({num_workers} Concurrent Workers, {DURATION_PER_SWEEP_SEC}s Duration) ---", flush=True)
    stop_event = threading.Event()
    write_counter_ref = {"val": 0, "lock": threading.Lock()}
    
    results_list = []
    
    def worker_loop():
        while not stop_event.is_set():
            try:
                op_type, elapsed_ms = execute_worker_operation(driver, node_pool, write_counter_ref)
                results_list.append((op_type, elapsed_ms))
            except Exception as err:
                print(f"[Worker Error] {err}", flush=True)
                
    start_time = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker_loop) for _ in range(num_workers)]
        time.sleep(DURATION_PER_SWEEP_SEC)
        stop_event.set()
        concurrent.futures.wait(futures)
        
    total_duration_sec = time.perf_counter() - start_time
    total_ops = len(results_list)
    qps = total_ops / total_duration_sec if total_duration_sec > 0 else 0
    
    all_latencies = [lat for _, lat in results_list] if results_list else [0.0]
    read_latencies = [lat for op, lat in results_list if op == "read"] or [0.0]
    write_latencies = [lat for op, lat in results_list if op == "write"] or [0.0]
    
    p50_total = float(np.percentile(all_latencies, 50))
    p95_total = float(np.percentile(all_latencies, 95))
    
    print(f"  Concurrency Tier: {num_workers} Workers", flush=True)
    print(f"  Total Operations: {total_ops:,} ops in {total_duration_sec:.2f}s", flush=True)
    print(f"  Throughput QPS:   {qps:,.2f} queries/sec", flush=True)
    print(f"  Latency p50:      {p50_total:.2f} ms | p95: {p95_total:.2f} ms", flush=True)
    
    return {
        "concurrent_workers": num_workers,
        "duration_sec": round(total_duration_sec, 2),
        "total_operations": total_ops,
        "throughput_qps": round(qps, 2),
        "read_count": len(read_latencies),
        "write_count": len(write_latencies),
        "p50_latency_ms": round(p50_total, 2),
        "p95_latency_ms": round(p95_total, 2),
        "read_p95_ms": round(float(np.percentile(read_latencies, 95)), 2),
        "write_p95_ms": round(float(np.percentile(write_latencies, 95)), 2)
    }

def main():
    if not uri or not user or not password:
        raise ValueError("Missing CognoDB credentials in environment (.env).")
        
    print("Loading node pool for mixed workload...", flush=True)
    node_pool = load_node_ids(nodes_csv)
    
    print(f"Connecting to CognoDB ({uri})...", flush=True)
    driver = get_driver(uri, (user, password))
    driver.verify_connectivity()
    print("Connected successfully.", flush=True)
    
    sweep_results = {}
    for workers in CONCURRENCY_LEVELS:
        key_name = f"workers_{workers}"
        sweep_results[key_name] = run_concurrency_sweep(driver, node_pool, workers)
        
    driver.close()
    
    telemetry = {
        "platform": "CognoDB",
        "workload": "mixed",
        "read_ratio": READ_RATIO,
        "write_ratio": round(1.0 - READ_RATIO, 2),
        "sweeps": sweep_results
    }
    
    os.makedirs(results_dir, exist_ok=True)
    with open(metrics_json, "w", encoding="utf-8") as f:
        json.dump(telemetry, f, indent=4)
        
    print("\n--- Mixed Workload Summary ---")
    for key, data in sweep_results.items():
        print(f"[{data['concurrent_workers']} Workers] Throughput: {data['throughput_qps']} QPS | p50: {data['p50_latency_ms']} ms | p95: {data['p95_latency_ms']} ms")
    print(f"Saved Results: {metrics_json}\n")

if __name__ == "__main__":
    main()
