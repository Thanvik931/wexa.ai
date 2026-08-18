import os
import gzip
import urllib.request
import pandas as pd

DATASET_URL = "https://snap.stanford.edu/data/soc-pokec-relationships.txt.gz"
DATASET_LICENSE = "Public Domain / SNAP Dataset (Stanford University)"
TARGET_EDGES = 200000

base_dir = os.path.dirname(os.path.abspath(__file__))
gz_path = os.path.join(base_dir, "soc-pokec-relationships.txt.gz")
nodes_csv = os.path.join(base_dir, "nodes.csv")
edges_csv = os.path.join(base_dir, "edges.csv")

def download_data(url, target_file):
    if not os.path.exists(target_file) or os.path.getsize(target_file) == 0:
        print(f"Downloading dataset from {url}...", flush=True)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp, open(target_file, "wb") as f_out:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                f_out.write(chunk)
        print("Download finished.", flush=True)
    else:
        print(f"Dataset archive already present ({os.path.getsize(target_file):,} bytes).", flush=True)

def process_graph_data(archive_path, max_edges):
    print(f"Extracting up to {max_edges:,} edges...", flush=True)
    edge_list = []
    node_set = set()

    with gzip.open(archive_path, "rt", encoding="utf-8") as f_in:
        for line in f_in:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tokens = line.split("\t")
            if len(tokens) >= 2:
                src, tgt = int(tokens[0]), int(tokens[1])
                edge_list.append((src, tgt))
                node_set.add(src)
                node_set.add(tgt)
                if len(edge_list) >= max_edges:
                    break

    edges_df = pd.DataFrame(edge_list, columns=["source", "target"])
    edges_df["type"] = "FRIEND_OF"
    edges_df.to_csv(edges_csv, index=False)

    nodes_df = pd.DataFrame(sorted(node_set), columns=["id"])
    nodes_df["label"] = "User"
    nodes_df.to_csv(nodes_csv, index=False)

    return len(nodes_df), len(edges_df)

def main():
    os.makedirs(base_dir, exist_ok=True)
    download_data(DATASET_URL, gz_path)
    total_nodes, total_edges = process_graph_data(gz_path, TARGET_EDGES)

    print("\n--- Dataset Summary ---")
    print(f"Source URL:   {DATASET_URL}")
    print(f"License:      {DATASET_LICENSE}")
    print(f"Node Count:   {total_nodes:,}")
    print(f"Edge Count:   {total_edges:,}")
    print(f"Nodes File:   {nodes_csv}")
    print(f"Edges File:   {edges_csv}\n")

if __name__ == "__main__":
    main()
