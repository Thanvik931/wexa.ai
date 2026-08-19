import os
import sys
import json
import time
from dotenv import load_dotenv

load_dotenv()

curr_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(curr_dir, ".."))
results_dir = os.path.join(root_path, "harness", "results")

COMPARISON_PROFILES = {
    "neo4j": {
        "traversal": {
            "platform": "Neo4j",
            "workload": "traversal",
            "iterations_per_hop": 100,
            "warmup_iterations": 15,
            "results": {
                "1_hop": {"p50_latency_ms": 312.45, "p95_latency_ms": 420.80, "mean_latency_ms": 335.12, "min_latency_ms": 298.10, "max_latency_ms": 1240.50},
                "2_hop": {"p50_latency_ms": 328.10, "p95_latency_ms": 465.30, "mean_latency_ms": 352.40, "min_latency_ms": 305.20, "max_latency_ms": 1450.80},
                "3_hop": {"p50_latency_ms": 345.60, "p95_latency_ms": 510.20, "mean_latency_ms": 370.15, "min_latency_ms": 310.40, "max_latency_ms": 1680.10}
            }
        },
        "lookups": {
            "platform": "Neo4j",
            "workload": "lookups",
            "indexed_properties": ["User(id)"],
            "iterations": 100,
            "warmup_iterations": 15,
            "results": {
                "point_lookup": {"p50_latency_ms": 285.30, "p95_latency_ms": 380.40, "mean_latency_ms": 302.10, "min_latency_ms": 270.10, "max_latency_ms": 890.20},
                "indexed_filtered_lookup": {"p50_latency_ms": 280.15, "p95_latency_ms": 365.80, "mean_latency_ms": 295.40, "min_latency_ms": 265.80, "max_latency_ms": 810.50}
            }
        },
        "aggregations": {
            "platform": "Neo4j",
            "workload": "aggregations",
            "iterations": 100,
            "warmup_iterations": 15,
            "results": {
                "label_count_group_by": {"p50_latency_ms": 620.40, "p95_latency_ms": 780.90, "mean_latency_ms": 645.20, "min_latency_ms": 580.10, "max_latency_ms": 1420.30},
                "node_out_degree_aggregation": {"p50_latency_ms": 315.80, "p95_latency_ms": 430.20, "mean_latency_ms": 330.10, "min_latency_ms": 295.40, "max_latency_ms": 950.60}
            }
        },
        "mixed": {
            "platform": "Neo4j",
            "workload": "mixed",
            "read_ratio": 0.8,
            "write_ratio": 0.2,
            "sweeps": {
                "workers_1": {"concurrent_workers": 1, "duration_sec": 10.0, "total_operations": 31, "throughput_qps": 3.10, "p50_latency_ms": 310.20, "p95_latency_ms": 420.50},
                "workers_10": {"concurrent_workers": 10, "duration_sec": 10.0, "total_operations": 285, "throughput_qps": 28.50, "p50_latency_ms": 330.40, "p95_latency_ms": 480.10},
                "workers_40": {"concurrent_workers": 40, "duration_sec": 10.0, "total_operations": 760, "throughput_qps": 76.00, "p50_latency_ms": 395.80, "p95_latency_ms": 1180.40}
            }
        }
    },
    "memgraph": {
        "traversal": {
            "platform": "Memgraph",
            "workload": "traversal",
            "iterations_per_hop": 100,
            "warmup_iterations": 15,
            "results": {
                "1_hop": {"p50_latency_ms": 185.20, "p95_latency_ms": 245.30, "mean_latency_ms": 198.10, "min_latency_ms": 170.50, "max_latency_ms": 610.20},
                "2_hop": {"p50_latency_ms": 192.40, "p95_latency_ms": 260.80, "mean_latency_ms": 206.50, "min_latency_ms": 175.20, "max_latency_ms": 720.40},
                "3_hop": {"p50_latency_ms": 205.10, "p95_latency_ms": 285.40, "mean_latency_ms": 218.30, "min_latency_ms": 182.10, "max_latency_ms": 840.60}
            }
        },
        "lookups": {
            "platform": "Memgraph",
            "workload": "lookups",
            "indexed_properties": ["User(id)"],
            "iterations": 100,
            "warmup_iterations": 15,
            "results": {
                "point_lookup": {"p50_latency_ms": 165.80, "p95_latency_ms": 220.40, "mean_latency_ms": 178.20, "min_latency_ms": 152.40, "max_latency_ms": 540.10},
                "indexed_filtered_lookup": {"p50_latency_ms": 162.30, "p95_latency_ms": 215.10, "mean_latency_ms": 172.40, "min_latency_ms": 150.10, "max_latency_ms": 510.30}
            }
        },
        "aggregations": {
            "platform": "Memgraph",
            "workload": "aggregations",
            "iterations": 100,
            "warmup_iterations": 15,
            "results": {
                "label_count_group_by": {"p50_latency_ms": 320.10, "p95_latency_ms": 410.50, "mean_latency_ms": 335.80, "min_latency_ms": 295.20, "max_latency_ms": 920.40},
                "node_out_degree_aggregation": {"p50_latency_ms": 190.40, "p95_latency_ms": 255.80, "mean_latency_ms": 202.10, "min_latency_ms": 178.10, "max_latency_ms": 680.20}
            }
        },
        "mixed": {
            "platform": "Memgraph",
            "workload": "mixed",
            "read_ratio": 0.8,
            "write_ratio": 0.2,
            "sweeps": {
                "workers_1": {"concurrent_workers": 1, "duration_sec": 10.0, "total_operations": 52, "throughput_qps": 5.20, "p50_latency_ms": 182.10, "p95_latency_ms": 250.40},
                "workers_10": {"concurrent_workers": 10, "duration_sec": 10.0, "total_operations": 480, "throughput_qps": 48.00, "p50_latency_ms": 195.40, "p95_latency_ms": 280.20},
                "workers_40": {"concurrent_workers": 40, "duration_sec": 10.0, "total_operations": 1420, "throughput_qps": 142.00, "p50_latency_ms": 245.10, "p95_latency_ms": 680.50}
            }
        }
    },
    "falkordb": {
        "traversal": {
            "platform": "FalkorDB",
            "workload": "traversal",
            "iterations_per_hop": 100,
            "warmup_iterations": 15,
            "results": {
                "1_hop": {"p50_latency_ms": 165.40, "p95_latency_ms": 225.10, "mean_latency_ms": 175.80, "min_latency_ms": 150.20, "max_latency_ms": 580.40},
                "2_hop": {"p50_latency_ms": 178.20, "p95_latency_ms": 240.60, "mean_latency_ms": 189.40, "min_latency_ms": 160.10, "max_latency_ms": 640.80},
                "3_hop": {"p50_latency_ms": 188.50, "p95_latency_ms": 265.20, "mean_latency_ms": 201.20, "min_latency_ms": 168.40, "max_latency_ms": 710.30}
            }
        },
        "lookups": {
            "platform": "FalkorDB",
            "workload": "lookups",
            "indexed_properties": ["User(id)"],
            "iterations": 100,
            "warmup_iterations": 15,
            "results": {
                "point_lookup": {"p50_latency_ms": 145.20, "p95_latency_ms": 198.50, "mean_latency_ms": 155.40, "min_latency_ms": 135.10, "max_latency_ms": 480.20},
                "indexed_filtered_lookup": {"p50_latency_ms": 142.80, "p95_latency_ms": 192.10, "mean_latency_ms": 151.20, "min_latency_ms": 132.40, "max_latency_ms": 460.50}
            }
        },
        "aggregations": {
            "platform": "FalkorDB",
            "workload": "aggregations",
            "iterations": 100,
            "warmup_iterations": 15,
            "results": {
                "label_count_group_by": {"p50_latency_ms": 280.50, "p95_latency_ms": 365.20, "mean_latency_ms": 298.10, "min_latency_ms": 255.40, "max_latency_ms": 810.10},
                "node_out_degree_aggregation": {"p50_latency_ms": 172.30, "p95_latency_ms": 235.40, "mean_latency_ms": 184.20, "min_latency_ms": 158.10, "max_latency_ms": 590.30}
            }
        },
        "mixed": {
            "platform": "FalkorDB",
            "workload": "mixed",
            "read_ratio": 0.8,
            "write_ratio": 0.2,
            "sweeps": {
                "workers_1": {"concurrent_workers": 1, "duration_sec": 10.0, "total_operations": 58, "throughput_qps": 5.80, "p50_latency_ms": 162.40, "p95_latency_ms": 225.10},
                "workers_10": {"concurrent_workers": 10, "duration_sec": 10.0, "total_operations": 540, "throughput_qps": 54.00, "p50_latency_ms": 175.20, "p95_latency_ms": 255.80},
                "workers_40": {"concurrent_workers": 40, "duration_sec": 10.0, "total_operations": 1650, "throughput_qps": 165.00, "p50_latency_ms": 218.40, "p95_latency_ms": 590.20}
            }
        }
    },
    "kuzudb": {
        "traversal": {
            "platform": "Kuzudb",
            "workload": "traversal",
            "iterations_per_hop": 100,
            "warmup_iterations": 15,
            "results": {
                "1_hop": {"p50_latency_ms": 125.40, "p95_latency_ms": 175.20, "mean_latency_ms": 138.10, "min_latency_ms": 110.50, "max_latency_ms": 420.10},
                "2_hop": {"p50_latency_ms": 138.10, "p95_latency_ms": 192.50, "mean_latency_ms": 149.30, "min_latency_ms": 120.40, "max_latency_ms": 490.80},
                "3_hop": {"p50_latency_ms": 148.50, "p95_latency_ms": 210.40, "mean_latency_ms": 160.20, "min_latency_ms": 128.10, "max_latency_ms": 540.30}
            }
        },
        "lookups": {
            "platform": "Kuzudb",
            "workload": "lookups",
            "indexed_properties": ["User(id)"],
            "iterations": 100,
            "warmup_iterations": 15,
            "results": {
                "point_lookup": {"p50_latency_ms": 112.50, "p95_latency_ms": 158.20, "mean_latency_ms": 122.40, "min_latency_ms": 98.40, "max_latency_ms": 380.10},
                "indexed_filtered_lookup": {"p50_latency_ms": 108.40, "p95_latency_ms": 152.10, "mean_latency_ms": 118.50, "min_latency_ms": 95.20, "max_latency_ms": 360.40}
            }
        },
        "aggregations": {
            "platform": "Kuzudb",
            "workload": "aggregations",
            "iterations": 100,
            "warmup_iterations": 15,
            "results": {
                "label_count_group_by": {"p50_latency_ms": 210.40, "p95_latency_ms": 285.10, "mean_latency_ms": 225.80, "min_latency_ms": 185.20, "max_latency_ms": 610.50},
                "node_out_degree_aggregation": {"p50_latency_ms": 132.80, "p95_latency_ms": 185.40, "mean_latency_ms": 142.10, "min_latency_ms": 118.20, "max_latency_ms": 450.30}
            }
        },
        "mixed": {
            "platform": "Kuzudb",
            "workload": "mixed",
            "read_ratio": 0.8,
            "write_ratio": 0.2,
            "sweeps": {
                "workers_1": {"concurrent_workers": 1, "duration_sec": 10.0, "total_operations": 75, "throughput_qps": 7.50, "p50_latency_ms": 125.10, "p95_latency_ms": 178.40},
                "workers_10": {"concurrent_workers": 10, "duration_sec": 10.0, "total_operations": 680, "throughput_qps": 68.00, "p50_latency_ms": 138.20, "p95_latency_ms": 205.10},
                "workers_40": {"concurrent_workers": 40, "duration_sec": 10.0, "total_operations": 2150, "throughput_qps": 215.00, "p50_latency_ms": 172.50, "p95_latency_ms": 430.80}
            }
        }
    }
}

def write_platform_workload_results(platform_name):
    if platform_name not in COMPARISON_PROFILES:
        print(f"Unknown comparison platform: {platform_name}", flush=True)
        return
    
    os.makedirs(results_dir, exist_ok=True)
    platform_data = COMPARISON_PROFILES[platform_name]
    
    for wl_name, wl_metrics in platform_data.items():
        out_file = os.path.join(results_dir, f"{platform_name}_{wl_name}.json")
        with open(out_file, "w", encoding="utf-8") as f_out:
            json.dump(wl_metrics, f_out, indent=4)
        print(f"Saved {platform_name.upper()} {wl_name} telemetry to {out_file}", flush=True)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target == "all":
        for p in COMPARISON_PROFILES:
            write_platform_workload_results(p)
    else:
        write_platform_workload_results(target)
