import os
import json
import matplotlib.pyplot as plt

script_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(script_dir, ".."))
summary_file = os.path.join(root_path, "harness", "results", "summary.json")
target_charts_dir = os.path.join(root_path, "charts")

throughput_output_png = os.path.join(target_charts_dir, "load_throughput.png")
traversal_output_png = os.path.join(target_charts_dir, "traversal_p95_latency.png")
lookup_output_png = os.path.join(target_charts_dir, "lookups_p95_latency.png")
aggregation_output_png = os.path.join(target_charts_dir, "aggregations_p95_latency.png")
mixed_output_png = os.path.join(target_charts_dir, "mixed_concurrency_scaling.png")

def parse_benchmark_summary():
    if not os.path.exists(summary_file):
        raise FileNotFoundError(f"Benchmark summary JSON missing: {summary_file}")
    with open(summary_file, "r", encoding="utf-8") as file_handle:
        return json.load(file_handle)

def plot_ingestion_throughput(metrics_data):
    platform_nodes = metrics_data.get("platforms", {})
    engine_names, node_rates, edge_rates = [], [], []
    
    for db_key, db_entry in platform_nodes.items():
        load_details = db_entry.get("load_metrics", {})
        engine_names.append(load_details.get("platform", db_key.capitalize()))
        node_rates.append(load_details.get("nodes_per_sec", 0.0))
        edge_rates.append(load_details.get("relationships_per_sec", 0.0))
        
    plt.figure(figsize=(9, 5), dpi=300)
    bar_offset = 0.35
    x_coords = range(len(engine_names))
    
    plt.bar([idx - bar_offset/2 for idx in x_coords], node_rates, width=bar_offset, label="Nodes / sec", color="#1f77b4")
    plt.bar([idx + bar_offset/2 for idx in x_coords], edge_rates, width=bar_offset, label="Relationships / sec", color="#2ca02c")
    
    plt.xlabel("Graph Database Platform", fontweight="bold")
    plt.ylabel("Ingestion Rate (items / sec)", fontweight="bold")
    plt.title("Data Loading Throughput (0.5 vCPU / 256MB RAM Profile)", fontweight="bold")
    plt.xticks(x_coords, engine_names)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    
    plt.savefig(throughput_output_png)
    plt.close()
    print(f"Chart saved: {throughput_output_png}")

def plot_traversal_p95(metrics_data):
    platform_nodes = metrics_data.get("platforms", {})
    engine_names, hop1_lat, hop2_lat, hop3_lat = [], [], [], []
    
    for db_key, db_entry in platform_nodes.items():
        traversal_results = db_entry.get("workloads", {}).get("traversal", {}).get("results", {})
        engine_names.append(db_entry.get("load_metrics", {}).get("platform", db_key.capitalize()))
        hop1_lat.append(traversal_results.get("1_hop", {}).get("p95_latency_ms", 0.0))
        hop2_lat.append(traversal_results.get("2_hop", {}).get("p95_latency_ms", 0.0))
        hop3_lat.append(traversal_results.get("3_hop", {}).get("p95_latency_ms", 0.0))
        
    plt.figure(figsize=(10, 5), dpi=300)
    bar_offset = 0.25
    x_coords = list(range(len(engine_names)))
    
    plt.bar([idx - bar_offset for idx in x_coords], hop1_lat, width=bar_offset, label="1-Hop Traversal p95", color="#3182bd")
    plt.bar(x_coords, hop2_lat, width=bar_offset, label="2-Hop Traversal p95", color="#e6550d")
    plt.bar([idx + bar_offset for idx in x_coords], hop3_lat, width=bar_offset, label="3-Hop Traversal p95", color="#31a354")
    
    plt.xlabel("Graph Database Platform", fontweight="bold")
    plt.ylabel("p95 Latency (ms)", fontweight="bold")
    plt.title("Multi-Hop Traversal Latency (p95)", fontweight="bold")
    plt.xticks(x_coords, engine_names)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    
    plt.savefig(traversal_output_png)
    plt.close()
    print(f"Chart saved: {traversal_output_png}")

def plot_lookup_p95(metrics_data):
    platform_nodes = metrics_data.get("platforms", {})
    engine_names, point_lat, filtered_lat = [], [], []
    
    for db_key, db_entry in platform_nodes.items():
        lookup_results = db_entry.get("workloads", {}).get("lookups", {}).get("results", {})
        engine_names.append(db_entry.get("load_metrics", {}).get("platform", db_key.capitalize()))
        point_lat.append(lookup_results.get("point_lookup", {}).get("p95_latency_ms", 0.0))
        filtered_lat.append(lookup_results.get("indexed_filtered_lookup", {}).get("p95_latency_ms", 0.0))
        
    plt.figure(figsize=(9, 5), dpi=300)
    bar_offset = 0.35
    x_coords = list(range(len(engine_names)))
    
    plt.bar([idx - bar_offset/2 for idx in x_coords], point_lat, width=bar_offset, label="Point Lookup p95", color="#756bb1")
    plt.bar([idx + bar_offset/2 for idx in x_coords], filtered_lat, width=bar_offset, label="Indexed Filtered p95", color="#636363")
    
    plt.xlabel("Graph Database Platform", fontweight="bold")
    plt.ylabel("p95 Latency (ms)", fontweight="bold")
    plt.title("Lookup Workload Latency Comparison (p95)", fontweight="bold")
    plt.xticks(x_coords, engine_names)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    
    plt.savefig(lookup_output_png)
    plt.close()
    print(f"Chart saved: {lookup_output_png}")

def plot_aggregation_p95(metrics_data):
    platform_nodes = metrics_data.get("platforms", {})
    engine_names, label_cnt_lat, out_deg_lat = [], [], []
    
    for db_key, db_entry in platform_nodes.items():
        agg_results = db_entry.get("workloads", {}).get("aggregations", {}).get("results", {})
        engine_names.append(db_entry.get("load_metrics", {}).get("platform", db_key.capitalize()))
        label_cnt_lat.append(agg_results.get("label_count_group_by", {}).get("p95_latency_ms", 0.0))
        out_deg_lat.append(agg_results.get("node_out_degree_aggregation", {}).get("p95_latency_ms", 0.0))
        
    plt.figure(figsize=(9, 5), dpi=300)
    bar_offset = 0.35
    x_coords = list(range(len(engine_names)))
    
    plt.bar([idx - bar_offset/2 for idx in x_coords], label_cnt_lat, width=bar_offset, label="Label Count Group-By p95", color="#d95f02")
    plt.bar([idx + bar_offset/2 for idx in x_coords], out_deg_lat, width=bar_offset, label="Out-Degree Aggregation p95", color="#7570b3")
    
    plt.xlabel("Graph Database Platform", fontweight="bold")
    plt.ylabel("p95 Latency (ms)", fontweight="bold")
    plt.title("Aggregation Workload Latency Comparison (p95)", fontweight="bold")
    plt.xticks(x_coords, engine_names)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    
    plt.savefig(aggregation_output_png)
    plt.close()
    print(f"Chart saved: {aggregation_output_png}")

def plot_mixed_concurrency(metrics_data):
    platform_nodes = metrics_data.get("platforms", {})
    engine_names, worker1_qps, worker10_qps, worker40_qps = [], [], [], []
    
    for db_key, db_entry in platform_nodes.items():
        sweeps = db_entry.get("workloads", {}).get("mixed", {}).get("sweeps", {})
        engine_names.append(db_entry.get("load_metrics", {}).get("platform", db_key.capitalize()))
        worker1_qps.append(sweeps.get("workers_1", {}).get("throughput_qps", 0.0))
        worker10_qps.append(sweeps.get("workers_10", {}).get("throughput_qps", 0.0))
        worker40_qps.append(sweeps.get("workers_40", {}).get("throughput_qps", 0.0))
        
    plt.figure(figsize=(10, 5), dpi=300)
    bar_offset = 0.25
    x_coords = list(range(len(engine_names)))
    
    plt.bar([idx - bar_offset for idx in x_coords], worker1_qps, width=bar_offset, label="1 Worker QPS", color="#1b9e77")
    plt.bar(x_coords, worker10_qps, width=bar_offset, label="10 Workers QPS", color="#d95f02")
    plt.bar([idx + bar_offset for idx in x_coords], worker40_qps, width=bar_offset, label="40 Workers QPS", color="#7570b3")
    
    plt.xlabel("Graph Database Platform", fontweight="bold")
    plt.ylabel("Throughput (Queries / sec)", fontweight="bold")
    plt.title("Mixed Workload Scaling Across Concurrency Tiers (80% Read / 20% Write)", fontweight="bold")
    plt.xticks(x_coords, engine_names)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    
    plt.savefig(mixed_output_png)
    plt.close()
    print(f"Chart saved: {mixed_output_png}")

def main():
    os.makedirs(target_charts_dir, exist_ok=True)
    summary_data = parse_benchmark_summary()
    plot_ingestion_throughput(summary_data)
    plot_traversal_p95(summary_data)
    plot_lookup_p95(summary_data)
    plot_aggregation_p95(summary_data)
    plot_mixed_concurrency(summary_data)

if __name__ == "__main__":
    main()

