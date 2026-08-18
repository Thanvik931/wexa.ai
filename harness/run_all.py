import os
import sys
import time
import json
import subprocess
import pandas as pd

# List of target comparison platforms to orchestrate
TARGET_PLATFORMS_CONFIG_LIST = ["cognodb"]

SCRIPT_LOCATION_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_DIRECTORY = os.path.abspath(os.path.join(SCRIPT_LOCATION_DIRECTORY, ".."))
LOADERS_DIRECTORY_PATH = os.path.join(PROJECT_ROOT_DIRECTORY, "loaders")
WORKLOADS_DIRECTORY_PATH = os.path.join(PROJECT_ROOT_DIRECTORY, "workloads")
HARNESS_RESULTS_DIRECTORY = os.path.join(PROJECT_ROOT_DIRECTORY, "harness", "results")

CONSOLIDATED_SUMMARY_JSON_PATH = os.path.join(HARNESS_RESULTS_DIRECTORY, "summary.json")
CONSOLIDATED_SUMMARY_CSV_PATH = os.path.join(HARNESS_RESULTS_DIRECTORY, "summary.csv")

def execute_python_subprocess_module(module_script_path, description_label):
    """Executes a benchmark loader or workload script as an isolated Python subprocess."""
    print(f"\n---> [Subprocess] Launching {description_label} ({os.path.basename(module_script_path)})...", flush=True)
    execution_start_timestamp = time.perf_counter()
    subprocess_process_result = subprocess.run(
        [sys.executable, module_script_path],
        cwd=PROJECT_ROOT_DIRECTORY,
        capture_output=False
    )
    execution_elapsed_seconds = time.perf_counter() - execution_start_timestamp
    if subprocess_process_result.returncode != 0:
        print(f"[Subprocess Failure] {description_label} exited with error code {subprocess_process_result.returncode}!", flush=True)
        return False, execution_elapsed_seconds
    print(f"[Subprocess Success] Completed {description_label} in {execution_elapsed_seconds:.2f} seconds.", flush=True)
    return True, execution_elapsed_seconds

def aggregate_platform_benchmark_results(platform_identifier_name):
    """Reads individual load and workload JSON output files for a platform and aggregates them."""
    platform_aggregated_metrics_dict = {
        "platform": platform_identifier_name.capitalize(),
        "load_metrics": {},
        "workloads": {}
    }
    
    # Read platform loader metrics
    loader_json_filepath = os.path.join(HARNESS_RESULTS_DIRECTORY, f"{platform_identifier_name}_load.json")
    if os.path.exists(loader_json_filepath):
        with open(loader_json_filepath, "r", encoding="utf-8") as loader_json_file:
            platform_aggregated_metrics_dict["load_metrics"] = json.load(loader_json_file)
            
    # Read workload metrics (traversal, lookups, aggregations, mixed)
    available_workload_types = ["traversal", "lookups", "aggregations", "mixed"]
    for workload_type_name in available_workload_types:
        workload_json_filepath = os.path.join(HARNESS_RESULTS_DIRECTORY, f"{platform_identifier_name}_{workload_type_name}.json")
        if os.path.exists(workload_json_filepath):
            with open(workload_json_filepath, "r", encoding="utf-8") as workload_json_file:
                platform_aggregated_metrics_dict["workloads"][workload_type_name] = json.load(workload_json_file)
                
    return platform_aggregated_metrics_dict

def generate_consolidated_tabular_csv(consolidated_summary_dictionary):
    """Flattens the consolidated benchmark metrics into a tabular pandas DataFrame and outputs CSV."""
    flattened_benchmark_rows_list = []
    
    for platform_key_name, platform_data_dict in consolidated_summary_dictionary.get("platforms", {}).items():
        platform_display_title = platform_data_dict.get("platform", platform_key_name)
        load_info = platform_data_dict.get("load_metrics", {})
        
        base_row_entry = {
            "Platform": platform_display_title,
            "Nodes_Loaded": load_info.get("nodes_loaded", 0),
            "Relationships_Loaded": load_info.get("relationships_loaded", 0),
            "Batch_Size": load_info.get("batch_size", 0),
            "Nodes_Per_Sec": load_info.get("nodes_per_sec", 0.0),
            "Relationships_Per_Sec": load_info.get("relationships_per_sec", 0.0),
            "Total_Load_Time_Sec": load_info.get("total_load_time_sec", 0.0),
        }
        
        workloads_info = platform_data_dict.get("workloads", {})
        
        # Extract Traversal Workload Metrics
        traversal_info = workloads_info.get("traversal", {}).get("results", {})
        for hop_level_key in ["1_hop", "2_hop", "3_hop"]:
            hop_metrics = traversal_info.get(hop_level_key, {})
            base_row_entry[f"Traversal_{hop_level_key}_p50_ms"] = hop_metrics.get("p50_latency_ms", None)
            base_row_entry[f"Traversal_{hop_level_key}_p95_ms"] = hop_metrics.get("p95_latency_ms", None)
            
        flattened_benchmark_rows_list.append(base_row_entry)
        
    summary_dataframe_table = pd.DataFrame(flattened_benchmark_rows_list)
    summary_dataframe_table.to_csv(CONSOLIDATED_SUMMARY_CSV_PATH, index=False)
    return len(summary_dataframe_table)

def run_benchmark_orchestrator_suite():
    """Main orchestration loop to run loaders, warm-up pass, and workloads for all target platforms."""
    print("==================================================", flush=True)
    print("       WEXA AI — CognoDB Benchmark Orchestrator    ", flush=True)
    print("==================================================", flush=True)
    print(f"Target Platforms Configured: {TARGET_PLATFORMS_CONFIG_LIST}", flush=True)
    
    all_platforms_summary_dictionary = {"platforms": {}}
    
    for platform_name_item in TARGET_PLATFORMS_CONFIG_LIST:
        print(f"\n==================================================", flush=True)
        print(f"       Processing Platform: {platform_name_item.upper()} ", flush=True)
        print("==================================================", flush=True)
        
        # 1. Run Data Loader
        loader_script_file_path = os.path.join(LOADERS_DIRECTORY_PATH, f"{platform_name_item}_loader.py")
        if os.path.exists(loader_script_file_path):
            loader_success, _ = execute_python_subprocess_module(
                loader_script_file_path, 
                f"{platform_name_item.upper()} Data Loader"
            )
            if not loader_success:
                print(f"[Warning] Skipping workloads for {platform_name_item} due to loader failure.", flush=True)
                continue
        else:
            print(f"[Notice] Loader script not found at {loader_script_file_path}. Skipping loader execution.", flush=True)
            
        # 2. Run Workload Scripts (traversal, lookups, aggregations, mixed)
        supported_workloads_list = [
            ("traversal", os.path.join(WORKLOADS_DIRECTORY_PATH, "traversal.py")),
            ("lookups", os.path.join(WORKLOADS_DIRECTORY_PATH, "lookups.py")),
            ("aggregations", os.path.join(WORKLOADS_DIRECTORY_PATH, "aggregations.py")),
            ("mixed", os.path.join(WORKLOADS_DIRECTORY_PATH, "mixed.py"))
        ]
        
        for workload_name_key, workload_script_file_path in supported_workloads_list:
            if os.path.exists(workload_script_file_path):
                execute_python_subprocess_module(
                    workload_script_file_path, 
                    f"{platform_name_item.upper()} {workload_name_key.capitalize()} Workload"
                )
            else:
                print(f"[Notice] Workload script '{workload_name_key}.py' not implemented yet. Skipping.", flush=True)
                
        # 3. Aggregate Platform Benchmark Results
        platform_metrics_data = aggregate_platform_benchmark_results(platform_name_item)
        all_platforms_summary_dictionary["platforms"][platform_name_item] = platform_metrics_data
        
    # Write Consolidated Summary JSON
    os.makedirs(HARNESS_RESULTS_DIRECTORY, exist_ok=True)
    with open(CONSOLIDATED_SUMMARY_JSON_PATH, "w", encoding="utf-8") as summary_json_file:
        json.dump(all_platforms_summary_dictionary, summary_json_file, indent=4)
        
    # Write Consolidated Summary CSV
    csv_rows_count = generate_consolidated_tabular_csv(all_platforms_summary_dictionary)
    
    print("\n==================================================", flush=True)
    print("      Orchestration Suite Execution Complete       ", flush=True)
    print("==================================================", flush=True)
    print(f"Summary JSON Generated: {CONSOLIDATED_SUMMARY_JSON_PATH}", flush=True)
    print(f"Summary CSV Generated:  {CONSOLIDATED_SUMMARY_CSV_PATH} ({csv_rows_count} rows)", flush=True)
    print("==================================================\n", flush=True)

if __name__ == "__main__":
    run_benchmark_orchestrator_suite()
