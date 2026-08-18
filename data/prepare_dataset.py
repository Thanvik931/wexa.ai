import os
import gzip
import urllib.request
import pandas as pd

DATASET_URL = "https://snap.stanford.edu/data/soc-pokec-relationships.txt.gz"
DATASET_LICENSE = "Public Domain / SNAP Dataset for Academic Research (Stanford University)"
TARGET_RELATIONSHIPS = 200000  # 200,000 relationships (100k - 500k range)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = SCRIPT_DIR
GZ_FILE_PATH = os.path.join(DATA_DIR, "soc-pokec-relationships.txt.gz")
NODES_CSV_PATH = os.path.join(DATA_DIR, "nodes.csv")
EDGES_CSV_PATH = os.path.join(DATA_DIR, "edges.csv")

def download_dataset(url, dest_path):
    if not os.path.exists(dest_path) or os.path.getsize(dest_path) == 0:
        print(f"Downloading dataset from {url}...", flush=True)
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
            chunk_size = 1024 * 1024
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
        print("Download complete.", flush=True)
    else:
        print(f"Dataset archive already present at {dest_path} ({os.path.getsize(dest_path):,} bytes)", flush=True)

def process_and_save(gz_path, num_edges):
    print(f"Processing dataset up to {num_edges:,} relationships...", flush=True)
    edges = []
    nodes = set()

    with gzip.open(gz_path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                src, tgt = int(parts[0]), int(parts[1])
                edges.append((src, tgt))
                nodes.add(src)
                nodes.add(tgt)
                if len(edges) >= num_edges:
                    break

    print(f"Writing {len(edges):,} edges to {EDGES_CSV_PATH}...", flush=True)
    df_edges = pd.DataFrame(edges, columns=["source", "target"])
    df_edges["type"] = "FRIEND_OF"
    df_edges.to_csv(EDGES_CSV_PATH, index=False)

    print(f"Writing {len(nodes):,} nodes to {NODES_CSV_PATH} (preserving referential integrity)...", flush=True)
    df_nodes = pd.DataFrame(sorted(list(nodes)), columns=["id"])
    df_nodes["label"] = "User"
    df_nodes.to_csv(NODES_CSV_PATH, index=False)

    return len(df_nodes), len(df_edges)

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    download_dataset(DATASET_URL, GZ_FILE_PATH)
    node_count, edge_count = process_and_save(GZ_FILE_PATH, TARGET_RELATIONSHIPS)

    print("\n==================================================", flush=True)
    print("        Dataset Acquisition & Prep Summary        ", flush=True)
    print("==================================================", flush=True)
    print(f"Source URL:         {DATASET_URL}", flush=True)
    print(f"License:            {DATASET_LICENSE}", flush=True)
    print(f"Exact Node Count:   {node_count:,}", flush=True)
    print(f"Relationship Count: {edge_count:,}", flush=True)
    print(f"Nodes File:         {NODES_CSV_PATH}", flush=True)
    print(f"Edges File:         {EDGES_CSV_PATH}", flush=True)
    print("==================================================\n", flush=True)

if __name__ == "__main__":
    main()
