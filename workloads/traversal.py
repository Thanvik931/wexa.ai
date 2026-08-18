import os
import time
import json
import random
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variable settings from .env file
load_dotenv()

# Non-default, descriptive environment configuration variables
COGNODB_CONNECTION_ENDPOINT_URI = os.getenv("COGNODB_URI")
COGNODB_ADMIN_USERNAME = os.getenv("COGNODB_USER")
COGNODB_ADMIN_PASSWORD = os.getenv("COGNODB_PASSWORD")

BENCHMARK_MEASURED_ITERATIONS = 100
BENCHMARK_WARMUP_ITERATIONS = 15

SCRIPT_LOCATION_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_DIRECTORY = os.path.abspath(os.path.join(SCRIPT_LOCATION_DIRECTORY, ".."))
NODES_CSV_SOURCE_FILEPATH = os.path.join(PROJECT_ROOT_DIRECTORY, "data", "nodes.csv")
HARNESS_RESULTS_DIRECTORY = os.path.join(PROJECT_ROOT_DIRECTORY, "harness", "results")
TRAVERSAL_METRICS_JSON_PATH = os.path.join(HARNESS_RESULTS_DIRECTORY, "cognodb_traversal.json")

def create_database_driver_instance(uri_endpoint_address, user_credentials_tuple):
    """Establishes driver connection instance to CognoDB GraphDatabase."""
    return GraphDatabase.driver(uri_endpoint_address, auth=user_credentials_tuple)

def extract_random_starting_node_ids(nodes_csv_filepath, sample_count=BENCHMARK_MEASURED_ITERATIONS + BENCHMARK_WARMUP_ITERATIONS):
    """Loads dataset nodes and returns a randomly sampled list of valid node IDs."""
    nodes_dataset_dataframe = pd.read_csv(nodes_csv_filepath)
    available_node_ids_list = nodes_dataset_dataframe["id"].tolist()
    random.seed(42)  # Fixed seed for reproducible node sampling across benchmark runs
    return random.sample(available_node_ids_list, min(sample_count, len(available_node_ids_list)))

def execute_single_traversal_query(neo4j_driver_instance, cypher_query_template, starting_user_node_id):
    """Executes a single traversal query and returns both client end-to-end latency and server execution time in ms."""
    client_query_start_timestamp = time.perf_counter()
    server_execution_time_ms = 0.0
    
    with neo4j_driver_instance.session() as active_database_session:
        query_result = active_database_session.run(cypher_query_template, {"start_id": int(starting_user_node_id)})
        result_summary_metadata = query_result.consume()
        
        # Extract server-side execution time from driver metadata if available
        if hasattr(result_summary_metadata, "result_available_after") and result_summary_metadata.result_available_after is not None:
            server_execution_time_ms = float(result_summary_metadata.result_available_after)
            
    client_elapsed_milliseconds = (time.perf_counter() - client_query_start_timestamp) * 1000.0
    return client_elapsed_milliseconds, server_execution_time_ms

def evaluate_hop_depth_traversal(neo4j_driver_instance, hop_depth_level, cypher_query_template, starting_node_ids_sample):
    """Evaluates traversal performance for a specific hop depth (warm-up + measured iterations)."""
    print(f"\n==================================================", flush=True)
    print(f"       Benchmarking {hop_depth_level}-Hop Traversal Depth         ", flush=True)
    print("==================================================", flush=True)
    print(f"[Cypher Query Sent]:\n{cypher_query_template.strip()}\n", flush=True)
    
    warmup_node_samples = starting_node_ids_sample[:BENCHMARK_WARMUP_ITERATIONS]
    measured_node_samples = starting_node_ids_sample[BENCHMARK_WARMUP_ITERATIONS : BENCHMARK_WARMUP_ITERATIONS + BENCHMARK_MEASURED_ITERATIONS]
    
    # 1. Warm-up Phase (heat database page cache and connection pools)
    print(f"Running {len(warmup_node_samples)} warm-up queries...", flush=True)
    for warmup_node_id in warmup_node_samples:
        execute_single_traversal_query(neo4j_driver_instance, cypher_query_template, warmup_node_id)
        
    # 2. Measured Benchmark Phase
    print(f"Running {len(measured_node_samples)} measured benchmark queries...", flush=True)
    client_measured_latencies_list_ms = []
    server_measured_latencies_list_ms = []
    
    for iteration_counter, measured_node_id in enumerate(measured_node_samples, start=1):
        client_ms, server_ms = execute_single_traversal_query(neo4j_driver_instance, cypher_query_template, measured_node_id)
        client_measured_latencies_list_ms.append(client_ms)
        server_measured_latencies_list_ms.append(server_ms)
        if iteration_counter % 25 == 0 or iteration_counter == len(measured_node_samples):
            print(f"  Progress: {iteration_counter}/{len(measured_node_samples)} queries complete...", flush=True)

    # 3. Calculate Percentiles for Client Latency (p50 median, p95 95th percentile)
    client_p50 = float(np.percentile(client_measured_latencies_list_ms, 50))
    client_p95 = float(np.percentile(client_measured_latencies_list_ms, 95))
    client_mean = float(np.mean(client_measured_latencies_list_ms))
    client_min = float(np.min(client_measured_latencies_list_ms))
    client_max = float(np.max(client_measured_latencies_list_ms))
    
    # Server-side execution percentiles
    server_p50 = float(np.percentile(server_measured_latencies_list_ms, 50))
    server_p95 = float(np.percentile(server_measured_latencies_list_ms, 95))
    server_mean = float(np.mean(server_measured_latencies_list_ms))
    
    print(f"  Client-Side (Total incl. Network RTT) -> p50: {client_p50:.2f} ms | p95: {client_p95:.2f} ms | mean: {client_mean:.2f} ms", flush=True)
    print(f"  Server-Side (DB Engine Only)          -> p50: {server_p50:.2f} ms | p95: {server_p95:.2f} ms | mean: {server_mean:.2f} ms", flush=True)
    
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

def run_traversal_benchmark_workload():
    """Main function to run 1-hop, 2-hop, and 3-hop traversal benchmarks against CognoDB."""
    if not COGNODB_CONNECTION_ENDPOINT_URI or not COGNODB_ADMIN_USERNAME or not COGNODB_ADMIN_PASSWORD:
        raise ValueError("Missing required CognoDB credentials in environment variables (COGNODB_URI, COGNODB_USER, COGNODB_PASSWORD)")
        
    print("Loading starting node IDs sample from dataset...", flush=True)
    total_required_samples = BENCHMARK_WARMUP_ITERATIONS + BENCHMARK_MEASURED_ITERATIONS
    starting_node_ids_pool = extract_random_starting_node_ids(NODES_CSV_SOURCE_FILEPATH, sample_count=total_required_samples)
    
    print(f"Connecting to CognoDB endpoint: {COGNODB_CONNECTION_ENDPOINT_URI}...", flush=True)
    cognodb_driver_connection = create_database_driver_instance(
        COGNODB_CONNECTION_ENDPOINT_URI, 
        (COGNODB_ADMIN_USERNAME, COGNODB_ADMIN_PASSWORD)
    )
    cognodb_driver_connection.verify_connectivity()
    print("Successfully connected to CognoDB instance.", flush=True)
    
    # Define Cypher traversal templates for 1-hop, 2-hop, and 3-hop graph paths
    cypher_traversal_queries_dict = {
        "1_hop": """MATCH (source_user_node:User {id: $start_id})-[rel_link1:FRIEND_OF]->(hop1_user_node:User) RETURN count(hop1_user_node) AS target_reach_count""",
        "2_hop": """MATCH (source_user_node:User {id: $start_id})-[rel_link1:FRIEND_OF]->(hop1_user_node:User)-[rel_link2:FRIEND_OF]->(hop2_user_node:User) RETURN count(DISTINCT hop2_user_node) AS target_reach_count""",
        "3_hop": """MATCH (source_user_node:User {id: $start_id})-[rel_link1:FRIEND_OF]->(hop1_user_node:User)-[rel_link2:FRIEND_OF]->(hop2_user_node:User)-[rel_link3:FRIEND_OF]->(hop3_user_node:User) RETURN count(DISTINCT hop3_user_node) AS target_reach_count"""
    }
    
    benchmark_hop_results_dict = {}
    for hop_level_name, cypher_statement_text in cypher_traversal_queries_dict.items():
        hop_numeric_depth = int(hop_level_name.split("_")[0])
        hop_performance_metrics = evaluate_hop_depth_traversal(
            cognodb_driver_connection, 
            hop_numeric_depth, 
            cypher_statement_text, 
            starting_node_ids_pool
        )
        benchmark_hop_results_dict[hop_level_name] = hop_performance_metrics
        
    cognodb_driver_connection.close()
    
    traversal_benchmark_telemetry = {
        "platform": "CognoDB",
        "workload": "traversal",
        "iterations_per_hop": BENCHMARK_MEASURED_ITERATIONS,
        "warmup_iterations": BENCHMARK_WARMUP_ITERATIONS,
        "results": benchmark_hop_results_dict
    }
    
    os.makedirs(HARNESS_RESULTS_DIRECTORY, exist_ok=True)
    with open(TRAVERSAL_METRICS_JSON_PATH, "w", encoding="utf-8") as metrics_json_file:
        json.dump(traversal_benchmark_telemetry, metrics_json_file, indent=4)
        
    print("\n==================================================", flush=True)
    print("      CognoDB Traversal Workload Summary          ", flush=True)
    print("==================================================", flush=True)
    for hop_level_key, metrics_data in benchmark_hop_results_dict.items():
        formatted_hop_title = hop_level_key.replace("_", "-").upper()
        print(f"[{formatted_hop_title}] Client p50: {metrics_data['p50_latency_ms']} ms | Client p95: {metrics_data['p95_latency_ms']} ms | Server Engine p50: {metrics_data['server_engine_p50_ms']} ms", flush=True)
    print(f"Results Output File: {TRAVERSAL_METRICS_JSON_PATH}", flush=True)
    print("==================================================\n", flush=True)

if __name__ == "__main__":
    run_traversal_benchmark_workload()
