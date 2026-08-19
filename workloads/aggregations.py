import os
import time
import json
import random
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

uri = os.getenv("COGNODB_URI")
user = os.getenv("COGNODB_USER")
password = os.getenv("COGNODB_PASSWORD")

NUM_ITERATIONS = 100
WARMUP_ITERATIONS = 15

base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(base_dir, ".."))
nodes_csv = os.path.join(project_root, "data", "nodes.csv")
results_dir = os.path.join(project_root, "harness", "results")
metrics_json = os.path.join(results_dir, "cognodb_aggregations.json")

def get_driver(uri_str, auth_tuple):
    return GraphDatabase.driver(uri_str, auth=auth_tuple)

def sample_start_nodes(csv_path, count=NUM_ITERATIONS + WARMUP_ITERATIONS):
    df = pd.read_csv(csv_path)
    node_ids = df["id"].tolist()
    random.seed(42)
    return random.sample(node_ids, min(count, len(node_ids)))

def run_single_aggregation(driver, cypher, start_id=None):
    t0 = time.perf_counter()
    server_ms = 0.0
    params = {"start_id": int(start_id)} if start_id is not None else {}
    
    with driver.session() as session:
        result = session.run(cypher, params)
        summary = result.consume()
        if hasattr(summary, "result_available_after") and summary.result_available_after is not None:
            server_ms = float(summary.result_available_after)
            
    client_ms = (time.perf_counter() - t0) * 1000.0
    return client_ms, server_ms

def benchmark_aggregation_type(driver, label_name, cypher, start_nodes=None):
    print(f"\n--- Benchmarking {label_name} ---", flush=True)
    print(f"[Query]: {cypher.strip()}\n", flush=True)
    
    if start_nodes:
        warmup_samples = start_nodes[:WARMUP_ITERATIONS]
        test_samples = start_nodes[WARMUP_ITERATIONS : WARMUP_ITERATIONS + NUM_ITERATIONS]
    else:
        warmup_samples = [None] * WARMUP_ITERATIONS
        test_samples = [None] * NUM_ITERATIONS
        
    print(f"Running {len(warmup_samples)} warm-up aggregation queries...", flush=True)
    for node_id in warmup_samples:
        run_single_aggregation(driver, cypher, node_id)
        
    print(f"Running {len(test_samples)} measured aggregation queries...", flush=True)
    client_latencies = []
    server_latencies = []
    
    for idx, node_id in enumerate(test_samples, start=1):
        client_ms, server_ms = run_single_aggregation(driver, cypher, node_id)
        client_latencies.append(client_ms)
        server_latencies.append(server_ms)
        if idx % 25 == 0 or idx == len(test_samples):
            print(f"  Progress: {idx}/{len(test_samples)} aggregation queries complete...", flush=True)

    client_p50 = float(np.percentile(client_latencies, 50))
    client_p95 = float(np.percentile(client_latencies, 95))
    client_mean = float(np.mean(client_latencies))
    client_min = float(np.min(client_latencies))
    client_max = float(np.max(client_latencies))
    
    server_p50 = float(np.percentile(server_latencies, 50))
    server_p95 = float(np.percentile(server_latencies, 95))
    server_mean = float(np.mean(server_latencies))
    
    print(f"  Client Latency -> p50: {client_p50:.2f} ms | p95: {client_p95:.2f} ms | mean: {client_mean:.2f} ms", flush=True)
    print(f"  Server Engine  -> p50: {server_p50:.2f} ms | p95: {server_p95:.2f} ms | mean: {server_mean:.2f} ms", flush=True)
    
    return {
        "p50_latency_ms": round(client_p50, 2),
        "p95_latency_ms": round(client_p95, 2),
        "mean_latency_ms": round(client_mean, 2),
        "min_latency_ms": round(client_min, 2),
        "max_latency_ms": round(client_max, 2),
        "server_engine_p50_ms": round(server_p50, 2),
        "server_engine_p95_ms": round(server_p95, 2),
        "server_engine_mean_ms": round(server_mean, 2)
    }

def main():
    if not uri or not user or not password:
        raise ValueError("Missing CognoDB credentials in environment (.env).")
        
    print("Loading sampled node IDs for aggregations...", flush=True)
    sample_pool = sample_start_nodes(nodes_csv)
    
    print(f"Connecting to CognoDB ({uri})...", flush=True)
    driver = get_driver(uri, (user, password))
    driver.verify_connectivity()
    print("Connected successfully.", flush=True)
    
    queries = {
        "label_count_group_by": "MATCH (u:User) RETURN u.label AS label_name, count(u) AS node_count",
        "node_out_degree_aggregation": "MATCH (u:User {id: $start_id})-[r:FRIEND_OF]->(f:User) RETURN u.id AS user_id, count(f) AS out_degree"
    }
    
    results = {}
    results["label_count_group_by"] = benchmark_aggregation_type(
        driver, "Label Count Group-By", queries["label_count_group_by"], start_nodes=None
    )
    results["node_out_degree_aggregation"] = benchmark_aggregation_type(
        driver, "Node Out-Degree Aggregation", queries["node_out_degree_aggregation"], start_nodes=sample_pool
    )
        
    driver.close()
    
    telemetry = {
        "platform": "CognoDB",
        "workload": "aggregations",
        "iterations": NUM_ITERATIONS,
        "warmup_iterations": WARMUP_ITERATIONS,
        "results": results
    }
    
    os.makedirs(results_dir, exist_ok=True)
    with open(metrics_json, "w", encoding="utf-8") as f:
        json.dump(telemetry, f, indent=4)
        
    print("\n--- Aggregations Summary ---")
    for key, data in results.items():
        print(f"[{key.upper()}] Client p50: {data['p50_latency_ms']} ms | Client p95: {data['p95_latency_ms']} ms")
    print(f"Saved Results: {metrics_json}\n")

if __name__ == "__main__":
    main()
