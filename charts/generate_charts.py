import os
import json
import matplotlib.pyplot as plt
import pandas as pd

SCRIPT_LOCATION_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_DIRECTORY = os.path.abspath(os.path.join(SCRIPT_LOCATION_DIRECTORY, ".."))
HARNESS_RESULTS_DIRECTORY = os.path.join(PROJECT_ROOT_DIRECTORY, "harness", "results")
SUMMARY_JSON_FILEPATH = os.path.join(HARNESS_RESULTS_DIRECTORY, "summary.json")
CHARTS_OUTPUT_DIRECTORY = os.path.join(PROJECT_ROOT_DIRECTORY, "charts")

LOAD_THROUGHPUT_CHART_FILEPATH = os.path.join(CHARTS_OUTPUT_DIRECTORY, "load_throughput.png")
TRAVERSAL_P95_CHART_FILEPATH = os.path.join(CHARTS_OUTPUT_DIRECTORY, "traversal_p95_latency.png")

def load_consolidated_summary_json(json_filepath):
    """Loads consolidated benchmark metrics from JSON output file."""
    if not os.path.exists(json_filepath):
        raise FileNotFoundError(f"Summary JSON file not found at {json_filepath}")
    with open(json_filepath, "r", encoding="utf-8") as summary_file_handle:
        return json.load(summary_file_handle)

def plot_data_ingestion_throughput(summary_metrics_dictionary):
    """Generates bar chart comparing node and relationship loading throughput across platforms."""
    platform_data_map = summary_metrics_dictionary.get("platforms", {})
    
    platform_names_list = []
    nodes_per_second_list = []
    relationships_per_second_list = []
    
    for platform_key_id, platform_payload in platform_data_map.items():
        platform_display_name = platform_payload.get("load_metrics", {}).get("platform", platform_key_id.capitalize())
        load_info = platform_payload.get("load_metrics", {})
        
        platform_names_list.append(platform_display_name)
        nodes_per_second_list.append(load_info.get("nodes_per_sec", 0.0))
        relationships_per_second_list.append(load_info.get("relationships_per_sec", 0.0))
        
    plt.figure(figsize=(9, 5), dpi=300)
    bar_width_val = 0.35
    x_indices = range(len(platform_names_list))
    
    plt.bar([x - bar_width_val/2 for x in x_indices], nodes_per_second_list, width=bar_width_val, label="Nodes / Sec", color="#2b5c8f")
    plt.bar([x + bar_width_val/2 for x in x_indices], relationships_per_second_list, width=bar_width_val, label="Relationships / Sec", color="#469b88")
    
    plt.xlabel("Graph Platform", fontsize=11, fontweight="bold")
    plt.ylabel("Ingestion Rate (Items / Sec)", fontsize=11, fontweight="bold")
    plt.title("Data Loading Ingestion Throughput Comparison", fontsize=13, fontweight="bold", pad=12)
    plt.xticks(x_indices, platform_names_list, fontsize=10)
    plt.legend(frameon=True, facecolor="#ffffff", edgecolor="#cccccc")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    
    plt.savefig(LOAD_THROUGHPUT_CHART_FILEPATH)
    plt.close()
    print(f"Generated chart: {LOAD_THROUGHPUT_CHART_FILEPATH}", flush=True)

def plot_traversal_p95_latencies(summary_metrics_dictionary):
    """Generates bar chart comparing 1-hop, 2-hop, and 3-hop p95 traversal latencies."""
    platform_data_map = summary_metrics_dictionary.get("platforms", {})
    
    platform_names_list = []
    hop1_p95_latencies_list = []
    hop2_p95_latencies_list = []
    hop3_p95_latencies_list = []
    
    for platform_key_id, platform_payload in platform_data_map.items():
        platform_display_name = platform_payload.get("load_metrics", {}).get("platform", platform_key_id.capitalize())
        traversal_results = platform_payload.get("workloads", {}).get("traversal", {}).get("results", {})
        
        platform_names_list.append(platform_display_name)
        hop1_p95_latencies_list.append(traversal_results.get("1_hop", {}).get("p95_latency_ms", 0.0))
        hop2_p95_latencies_list.append(traversal_results.get("2_hop", {}).get("p95_latency_ms", 0.0))
        hop3_p95_latencies_list.append(traversal_results.get("3_hop", {}).get("p95_latency_ms", 0.0))
        
    plt.figure(figsize=(10, 5), dpi=300)
    bar_width_val = 0.25
    x_indices = list(range(len(platform_names_list)))
    
    plt.bar([x - bar_width_val for x in x_indices], hop1_p95_latencies_list, width=bar_width_val, label="1-Hop p95", color="#3b6998")
    plt.bar(x_indices, hop2_p95_latencies_list, width=bar_width_val, label="2-Hop p95", color="#e07a5f")
    plt.bar([x + bar_width_val for x in x_indices], hop3_p95_latencies_list, width=bar_width_val, label="3-Hop p95", color="#81b29a")
    
    plt.xlabel("Graph Platform", fontsize=11, fontweight="bold")
    plt.ylabel("p95 Latency (ms)", fontsize=11, fontweight="bold")
    plt.title("Graph Traversal Workload — p95 Tail Latency Comparison", fontsize=13, fontweight="bold", pad=12)
    plt.xticks(x_indices, platform_names_list, fontsize=10)
    plt.legend(frameon=True, facecolor="#ffffff", edgecolor="#cccccc")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    
    plt.savefig(TRAVERSAL_P95_CHART_FILEPATH)
    plt.close()
    print(f"Generated chart: {TRAVERSAL_P95_CHART_FILEPATH}", flush=True)

def generate_all_benchmark_charts():
    """Main execution function to load results and output visualization charts."""
    os.makedirs(CHARTS_OUTPUT_DIRECTORY, exist_ok=True)
    summary_data_dictionary = load_consolidated_summary_json(SUMMARY_JSON_FILEPATH)
    
    plot_data_ingestion_throughput(summary_data_dictionary)
    plot_traversal_p95_latencies(summary_data_dictionary)
    print("All benchmark charts successfully generated in /charts directory.", flush=True)

if __name__ == "__main__":
    generate_all_benchmark_charts()
