import os
import time
import json
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase, exceptions

load_dotenv()

uri = os.getenv("COGNODB_URI")
user = os.getenv("COGNODB_USER")
password = os.getenv("COGNODB_PASSWORD")

DEFAULT_BATCH_SIZE = 1000
MAX_RETRIES = 5

base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(base_dir, ".."))
nodes_csv = os.path.join(project_root, "data", "nodes.csv")
edges_csv = os.path.join(project_root, "data", "edges.csv")
results_dir = os.path.join(project_root, "harness", "results")
metrics_json = os.path.join(results_dir, "cognodb_load.json")

def get_driver(uri_str, auth_tuple):
    return GraphDatabase.driver(uri_str, auth=auth_tuple)

def run_query_retry(driver, cypher, params=None, retries=MAX_RETRIES):
    for attempt in range(1, retries + 1):
        try:
            with driver.session() as session:
                session.run(cypher, params or {})
                return
        except (exceptions.ServiceUnavailable, exceptions.SessionExpired, exceptions.TransientError) as err:
            if attempt == retries:
                raise err
            wait_time = 2 ** attempt
            print(f"[Retry] Transient error: {err}. Retrying ({attempt}/{retries}) in {wait_time}s...", flush=True)
            time.sleep(wait_time)

def ensure_indexes(driver):
    print("Setting up index on User(id)...", flush=True)
    cypher = "CREATE INDEX user_id_lookup_idx IF NOT EXISTS FOR (u:User) ON (u.id)"
    try:
        run_query_retry(driver, cypher)
    except Exception as e:
        print(f"[Index Notice] {e}", flush=True)

def load_nodes(driver, df, batch_size):
    records = df.to_dict(orient="records")
    total = len(records)
    print(f"Loading {total:,} nodes in batches of {batch_size:,}...", flush=True)
    
    cypher = """
    UNWIND $batch AS row
    MERGE (u:User {id: row.id})
    SET u.label = row.label
    """
    
    start_time = time.perf_counter()
    for i in range(0, total, batch_size):
        chunk = records[i : i + batch_size]
        run_query_retry(driver, cypher, {"batch": chunk})
    
    return time.perf_counter() - start_time

def load_edges(driver, df, batch_size):
    records = df.to_dict(orient="records")
    total = len(records)
    print(f"Loading {total:,} relationships in batches of {batch_size:,}...", flush=True)
    
    cypher = """
    UNWIND $batch AS row
    MATCH (src:User {id: row.source})
    MATCH (tgt:User {id: row.target})
    MERGE (src)-[r:FRIEND_OF]->(tgt)
    """
    
    start_time = time.perf_counter()
    for i in range(0, total, batch_size):
        chunk = records[i : i + batch_size]
        run_query_retry(driver, cypher, {"batch": chunk})
    
    return time.perf_counter() - start_time

def main(batch_size=DEFAULT_BATCH_SIZE):
    if not uri or not user or not password:
        raise ValueError("Missing CogODB credentials in environment (.env).")
    
    print("Reading data CSVs...", flush=True)
    nodes_df = pd.read_csv(nodes_csv)
    edges_df = pd.read_csv(edges_csv)
    
    node_count = len(nodes_df)
    edge_count = len(edges_df)
    print(f"Loaded {node_count:,} nodes and {edge_count:,} edges.", flush=True)
    
    print(f"Connecting to CognoDB ({uri})...", flush=True)
    driver = get_driver(uri, (user, password))
    driver.verify_connectivity()
    print("Connected successfully.", flush=True)
    
    ensure_indexes(driver)
    
    start_all = time.perf_counter()
    
    node_time = load_nodes(driver, nodes_df, batch_size)
    edge_time = load_edges(driver, edges_df, batch_size)
    
    total_time = time.perf_counter() - start_all
    driver.close()
    
    nodes_per_sec = node_count / node_time if node_time > 0 else 0
    edges_per_sec = edge_count / edge_time if edge_time > 0 else 0
    
    metrics = {
        "platform": "CognoDB",
        "nodes_loaded": node_count,
        "relationships_loaded": edge_count,
        "batch_size": batch_size,
        "nodes_per_sec": round(nodes_per_sec, 2),
        "relationships_per_sec": round(edges_per_sec, 2),
        "total_load_time_sec": round(total_time, 2),
        "node_load_time_sec": round(node_time, 2),
        "relationship_load_time_sec": round(edge_time, 2)
    }
    
    os.makedirs(results_dir, exist_ok=True)
    with open(metrics_json, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)
        
    print("\n--- CognoDB Load Summary ---")
    print(f"Nodes Loaded:        {node_count:,}")
    print(f"Edges Loaded:        {edge_count:,}")
    print(f"Nodes / sec:         {nodes_per_sec:,.2f}")
    print(f"Edges / sec:         {edges_per_sec:,.2f}")
    print(f"Total Load Time:     {total_time:.2f}s")
    print(f"Saved Results:       {metrics_json}\n")

if __name__ == "__main__":
    main()
