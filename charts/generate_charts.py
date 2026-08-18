import os
import json
import matplotlib.pyplot as plt

base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(base_dir, ".."))
summary_json = os.path.join(project_root, "harness", "results", "summary.json")
charts_dir = os.path.join(project_root, "charts")

throughput_png = os.path.join(charts_dir, "load_throughput.png")
traversal_p95_png = os.path.join(charts_dir, "traversal_p95_latency.png")

def load_summary():
    if not os.path.exists(summary_json):
        raise FileNotFoundError(f"Summary JSON missing at {summary_json}")
    with open(summary_json, "r", encoding="utf-8") as f:
        return json.load(f)

def plot_throughput(data):
    platforms_map = data.get("platforms", {})
    names, nodes_sec, edges_sec = [], [], []
    
    for key, val in platforms_map.items():
        load_info = val.get("load_metrics", {})
        names.append(load_info.get("platform", key.capitalize()))
        nodes_sec.append(load_info.get("nodes_per_sec", 0.0))
        edges_sec.append(load_info.get("relationships_per_sec", 0.0))
        
    plt.figure(figsize=(8, 4.5), dpi=300)
    width = 0.35
    x = range(len(names))
    
    plt.bar([i - width/2 for i in x], nodes_sec, width=width, label="Nodes / sec", color="#2b5c8f")
    plt.bar([i + width/2 for i in x], edges_sec, width=width, label="Relationships / sec", color="#469b88")
    
    plt.xlabel("Platform", fontweight="bold")
    plt.ylabel("Ingestion Throughput (items/sec)", fontweight="bold")
    plt.title("Data Loading Throughput Comparison", fontweight="bold")
    plt.xticks(x, names)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    
    plt.savefig(throughput_png)
    plt.close()
    print(f"Generated chart: {throughput_png}")

def plot_traversal(data):
    platforms_map = data.get("platforms", {})
    names, hop1_p95, hop2_p95, hop3_p95 = [], [], [], []
    
    for key, val in platforms_map.items():
        res = val.get("workloads", {}).get("traversal", {}).get("results", {})
        names.append(val.get("load_metrics", {}).get("platform", key.capitalize()))
        hop1_p95.append(res.get("1_hop", {}).get("p95_latency_ms", 0.0))
        hop2_p95.append(res.get("2_hop", {}).get("p95_latency_ms", 0.0))
        hop3_p95.append(res.get("3_hop", {}).get("p95_latency_ms", 0.0))
        
    plt.figure(figsize=(9, 4.5), dpi=300)
    width = 0.25
    x = list(range(len(names)))
    
    plt.bar([i - width for i in x], hop1_p95, width=width, label="1-Hop p95", color="#3b6998")
    plt.bar(x, hop2_p95, width=width, label="2-Hop p95", color="#e07a5f")
    plt.bar([i + width for i in x], hop3_p95, width=width, label="3-Hop p95", color="#81b29a")
    
    plt.xlabel("Platform", fontweight="bold")
    plt.ylabel("p95 Latency (ms)", fontweight="bold")
    plt.title("Graph Traversal Workload — p95 Latency", fontweight="bold")
    plt.xticks(x, names)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    
    plt.savefig(traversal_p95_png)
    plt.close()
    print(f"Generated chart: {traversal_p95_png}")

def main():
    os.makedirs(charts_dir, exist_ok=True)
    data = load_summary()
    plot_throughput(data)
    plot_traversal(data)

if __name__ == "__main__":
    main()
