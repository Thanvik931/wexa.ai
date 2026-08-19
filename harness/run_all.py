import os
import sys
import time
import json
import subprocess
import pandas as pd

PLATFORMS = ["cognodb", "neo4j", "memgraph", "falkordb", "kuzudb"]

base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(base_dir, ".."))
loaders_dir = os.path.join(project_root, "loaders")
workloads_dir = os.path.join(project_root, "workloads")
results_dir = os.path.join(project_root, "harness", "results")

summary_json = os.path.join(results_dir, "summary.json")
summary_csv = os.path.join(results_dir, "summary.csv")

def run_subprocess(script_path, label, extra_args=None):
    print(f"\n---> Running {label} ({os.path.basename(script_path)})...", flush=True)
    t0 = time.perf_counter()
    cmd = [sys.executable, script_path]
    if extra_args:
        cmd.extend(extra_args)
    res = subprocess.run(cmd, cwd=project_root, capture_output=False)
    elapsed = time.perf_counter() - t0
    
    if res.returncode != 0:
        print(f"[Error] {label} failed with exit code {res.returncode}.", flush=True)
        return False, elapsed
    print(f"[Done] {label} finished in {elapsed:.2f}s.", flush=True)
    return True, elapsed

def collect_results(platform):
    metrics = {
        "platform": platform.capitalize(),
        "load_metrics": {},
        "workloads": {}
    }
    
    loader_json = os.path.join(results_dir, f"{platform}_load.json")
    if os.path.exists(loader_json):
        with open(loader_json, "r", encoding="utf-8") as f:
            metrics["load_metrics"] = json.load(f)
            
    for wl in ["traversal", "lookups", "aggregations", "mixed"]:
        wl_json = os.path.join(results_dir, f"{platform}_{wl}.json")
        if os.path.exists(wl_json):
            with open(wl_json, "r", encoding="utf-8") as f:
                metrics["workloads"][wl] = json.load(f)
                
    return metrics

def export_summary_csv(summary_data):
    rows = []
    
    for platform_key, p_data in summary_data.get("platforms", {}).items():
        load_info = p_data.get("load_metrics", {})
        
        row = {
            "Platform": p_data.get("platform", platform_key),
            "Nodes_Loaded": load_info.get("nodes_loaded", 0),
            "Relationships_Loaded": load_info.get("relationships_loaded", 0),
            "Batch_Size": load_info.get("batch_size", 0),
            "Nodes_Per_Sec": load_info.get("nodes_per_sec", 0.0),
            "Relationships_Per_Sec": load_info.get("relationships_per_sec", 0.0),
            "Total_Load_Time_Sec": load_info.get("total_load_time_sec", 0.0),
        }
        
        workloads = p_data.get("workloads", {})
        traversal_res = workloads.get("traversal", {}).get("results", {})
        
        for hop in ["1_hop", "2_hop", "3_hop"]:
            hop_data = traversal_res.get(hop, {})
            row[f"Traversal_{hop}_p50_ms"] = hop_data.get("p50_latency_ms", None)
            row[f"Traversal_{hop}_p95_ms"] = hop_data.get("p95_latency_ms", None)
            
        rows.append(row)
        
    df = pd.DataFrame(rows)
    df.to_csv(summary_csv, index=False)
    return len(df)

def main():
    print("==================================================", flush=True)
    print("       WEXA AI — Graph DB Benchmark Harness       ", flush=True)
    print("==================================================", flush=True)
    
    summary = {"platforms": {}}
    
    for platform in PLATFORMS:
        print(f"\n---> Platform: {platform.upper()}", flush=True)
        
        loader_script = os.path.join(loaders_dir, f"{platform}_loader.py")
        if os.path.exists(loader_script):
            success, _ = run_subprocess(loader_script, f"{platform.upper()} Loader")
            if not success:
                print(f"Skipping workloads for {platform} due to loader error.", flush=True)
                continue
        else:
            print(f"Loader script not found for {platform}. Skipping loader.", flush=True)
            
        if platform == "cognodb":
            workloads = [
                ("traversal", os.path.join(workloads_dir, "traversal.py")),
                ("lookups", os.path.join(workloads_dir, "lookups.py")),
                ("aggregations", os.path.join(workloads_dir, "aggregations.py")),
                ("mixed", os.path.join(workloads_dir, "mixed.py"))
            ]
            for name, script in workloads:
                if os.path.exists(script):
                    run_subprocess(script, f"{platform.upper()} {name.capitalize()}")
        else:
            comp_script = os.path.join(workloads_dir, "run_comparison_workloads.py")
            if os.path.exists(comp_script):
                run_subprocess(comp_script, f"{platform.upper()} Workloads", [platform])
                
        summary["platforms"][platform] = collect_results(platform)
        
    os.makedirs(results_dir, exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
        
    count = export_summary_csv(summary)
    
    print("\n==================================================", flush=True)
    print(f"Summary JSON: {summary_json}")
    print(f"Summary CSV:  {summary_csv} ({count} row)")
    print("==================================================\n", flush=True)

if __name__ == "__main__":
    main()
