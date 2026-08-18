import os
import time
import json
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase, exceptions

# Load environment variable settings from .env file
load_dotenv()

# Non-default, descriptive environment configuration variables
COGNODB_CONNECTION_ENDPOINT_URI = os.getenv("COGNODB_URI")
COGNODB_ADMIN_USERNAME = os.getenv("COGNODB_USER")
COGNODB_ADMIN_PASSWORD = os.getenv("COGNODB_PASSWORD")
DEFAULT_BATCH_CHUNK_SIZE = 1000
MAX_TRANSIENT_RETRY_ATTEMPTS = 5

SCRIPT_LOCATION_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_DIRECTORY = os.path.abspath(os.path.join(SCRIPT_LOCATION_DIRECTORY, ".."))
NODES_CSV_SOURCE_FILEPATH = os.path.join(PROJECT_ROOT_DIRECTORY, "data", "nodes.csv")
EDGES_CSV_SOURCE_FILEPATH = os.path.join(PROJECT_ROOT_DIRECTORY, "data", "edges.csv")
HARNESS_RESULTS_DIRECTORY = os.path.join(PROJECT_ROOT_DIRECTORY, "harness", "results")
COGNODB_LOAD_METRICS_JSON_PATH = os.path.join(HARNESS_RESULTS_DIRECTORY, "cognodb_load.json")

def create_database_driver_instance(uri_endpoint_address, user_credentials_tuple):
    """Establishes driver connection instance to CognoDB GraphDatabase."""
    return GraphDatabase.driver(uri_endpoint_address, auth=user_credentials_tuple)

def execute_cypher_query_with_retry(neo4j_driver_instance, cypher_statement_text, query_parameters_dict=None, max_retry_limit=MAX_TRANSIENT_RETRY_ATTEMPTS):
    """Executes a Cypher query with automatic exponential backoff retry for transient network/DB errors."""
    for current_attempt_number in range(1, max_retry_limit + 1):
        try:
            with neo4j_driver_instance.session() as active_database_session:
                active_database_session.run(cypher_statement_text, query_parameters_dict or {})
                return
        except (exceptions.ServiceUnavailable, exceptions.SessionExpired, exceptions.TransientError) as transient_connection_error:
            if current_attempt_number == max_retry_limit:
                raise transient_connection_error
            exponential_backoff_seconds = 2 ** current_attempt_number
            print(f"[Retry Warning] Transient DB error: {transient_connection_error}. Retrying attempt {current_attempt_number}/{max_retry_limit} after {exponential_backoff_seconds}s...", flush=True)
            time.sleep(exponential_backoff_seconds)

def prepare_database_schema_indexing(neo4j_driver_instance):
    """Creates index on User(id) to ensure ultra-fast relationship link lookups."""
    print("Preparing schema index on User(id) for fast edge resolution...", flush=True)
    create_index_cypher = "CREATE INDEX user_id_lookup_idx IF NOT EXISTS FOR (user_node:User) ON (user_node.id)"
    try:
        execute_cypher_query_with_retry(neo4j_driver_instance, create_index_cypher)
    except Exception as index_creation_exception:
        print(f"[Index Notice] Schema index statement result: {index_creation_exception}", flush=True)

def ingest_node_records_in_batches(neo4j_driver_instance, nodes_dataset_dataframe, batch_size_chunk):
    """Loads nodes into CognoDB using batched UNWIND Cypher queries."""
    node_records_dictionary_list = nodes_dataset_dataframe.to_dict(orient="records")
    total_nodes_to_process = len(node_records_dictionary_list)
    print(f"Ingesting {total_nodes_to_process:,} nodes in batches of {batch_size_chunk:,}...", flush=True)
    
    batched_node_cypher_query = """
    UNWIND $batch_records AS node_item
    MERGE (user_node:User {id: node_item.id})
    SET user_node.label = node_item.label
    """
    
    node_ingestion_start_time = time.perf_counter()
    for batch_offset_index in range(0, total_nodes_to_process, batch_size_chunk):
        current_node_batch_chunk = node_records_dictionary_list[batch_offset_index : batch_offset_index + batch_size_chunk]
        execute_cypher_query_with_retry(neo4j_driver_instance, batched_node_cypher_query, {"batch_records": current_node_batch_chunk})
    
    node_ingestion_total_duration = time.perf_counter() - node_ingestion_start_time
    return node_ingestion_total_duration

def ingest_relationship_records_in_batches(neo4j_driver_instance, edges_dataset_dataframe, batch_size_chunk):
    """Loads relationships into CognoDB using batched UNWIND Cypher queries."""
    edge_records_dictionary_list = edges_dataset_dataframe.to_dict(orient="records")
    total_edges_to_process = len(edge_records_dictionary_list)
    print(f"Ingesting {total_edges_to_process:,} relationships in batches of {batch_size_chunk:,}...", flush=True)
    
    batched_edge_cypher_query = """
    UNWIND $batch_records AS edge_item
    MATCH (source_user_node:User {id: edge_item.source})
    MATCH (target_user_node:User {id: edge_item.target})
    MERGE (source_user_node)-[friend_relationship:FRIEND_OF]->(target_user_node)
    """
    
    edge_ingestion_start_time = time.perf_counter()
    for batch_offset_index in range(0, total_edges_to_process, batch_size_chunk):
        current_edge_batch_chunk = edge_records_dictionary_list[batch_offset_index : batch_offset_index + batch_size_chunk]
        execute_cypher_query_with_retry(neo4j_driver_instance, batched_edge_cypher_query, {"batch_records": current_edge_batch_chunk})
    
    edge_ingestion_total_duration = time.perf_counter() - edge_ingestion_start_time
    return edge_ingestion_total_duration

def execute_cognodb_benchmark_data_loader(custom_batch_chunk_size=DEFAULT_BATCH_CHUNK_SIZE):
    """Main execution function to orchestrate CognoDB data ingestion and benchmark timing."""
    if not COGNODB_CONNECTION_ENDPOINT_URI or not COGNODB_ADMIN_USERNAME or not COGNODB_ADMIN_PASSWORD:
        raise ValueError("Missing required CognoDB credentials in environment variables (COGNODB_URI, COGNODB_USER, COGNODB_PASSWORD)")
    
    print("Reading dataset CSV files from data directory...", flush=True)
    nodes_dataset_df = pd.read_csv(NODES_CSV_SOURCE_FILEPATH)
    edges_dataset_df = pd.read_csv(EDGES_CSV_SOURCE_FILEPATH)
    
    nodes_quantity = len(nodes_dataset_df)
    edges_quantity = len(edges_dataset_df)
    print(f"Dataset loaded successfully: {nodes_quantity:,} nodes and {edges_quantity:,} edges.", flush=True)
    
    print(f"Connecting to CognoDB endpoint: {COGNODB_CONNECTION_ENDPOINT_URI}...", flush=True)
    cognodb_driver_connection = create_database_driver_instance(
        COGNODB_CONNECTION_ENDPOINT_URI, 
        (COGNODB_ADMIN_USERNAME, COGNODB_ADMIN_PASSWORD)
    )
    cognodb_driver_connection.verify_connectivity()
    print("Successfully connected to CognoDB instance.", flush=True)
    
    prepare_database_schema_indexing(cognodb_driver_connection)
    
    total_benchmark_start_timer = time.perf_counter()
    
    nodes_ingestion_elapsed_sec = ingest_node_records_in_batches(cognodb_driver_connection, nodes_dataset_df, custom_batch_chunk_size)
    edges_ingestion_elapsed_sec = ingest_relationship_records_in_batches(cognodb_driver_connection, edges_dataset_df, custom_batch_chunk_size)
    
    total_benchmark_elapsed_sec = time.perf_counter() - total_benchmark_start_timer
    cognodb_driver_connection.close()
    
    nodes_per_second_rate = nodes_quantity / nodes_ingestion_elapsed_sec if nodes_ingestion_elapsed_sec > 0 else 0
    relationships_per_second_rate = edges_quantity / edges_ingestion_elapsed_sec if edges_ingestion_elapsed_sec > 0 else 0
    
    benchmark_results_telemetry = {
        "platform": "CognoDB",
        "nodes_loaded": nodes_quantity,
        "relationships_loaded": edges_quantity,
        "batch_size": custom_batch_chunk_size,
        "nodes_per_sec": round(nodes_per_second_rate, 2),
        "relationships_per_sec": round(relationships_per_second_rate, 2),
        "total_load_time_sec": round(total_benchmark_elapsed_sec, 2),
        "node_load_time_sec": round(nodes_ingestion_elapsed_sec, 2),
        "relationship_load_time_sec": round(edges_ingestion_elapsed_sec, 2)
    }
    
    os.makedirs(HARNESS_RESULTS_DIRECTORY, exist_ok=True)
    with open(COGNODB_LOAD_METRICS_JSON_PATH, "w", encoding="utf-8") as metrics_json_file:
        json.dump(benchmark_results_telemetry, metrics_json_file, indent=4)
        
    print("\n==================================================", flush=True)
    print("           CognoDB Data Loader Summary            ", flush=True)
    print("==================================================", flush=True)
    print(f"Nodes Loaded:          {nodes_quantity:,}", flush=True)
    print(f"Relationships Loaded:  {edges_quantity:,}", flush=True)
    print(f"Batch Size:            {custom_batch_chunk_size:,}", flush=True)
    print(f"Nodes / Sec:           {nodes_per_second_rate:,.2f}", flush=True)
    print(f"Relationships / Sec:   {relationships_per_second_rate:,.2f}", flush=True)
    print(f"Total Load Time:       {total_benchmark_elapsed_sec:.2f} seconds", flush=True)
    print(f"Results File:          {COGNODB_LOAD_METRICS_JSON_PATH}", flush=True)
    print("==================================================\n", flush=True)

if __name__ == "__main__":
    execute_cognodb_benchmark_data_loader()
