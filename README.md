# WEXA AI — CognoDB Benchmark

An empirical performance benchmarking suite evaluating graph database throughput and latency metrics across data loading and graph traversal workloads.

---

## 📊 Benchmark Results Summary

### 1. Data Ingestion & Loading Throughput

| Platform | Nodes Loaded | Relationships Loaded | Batch Size | Nodes / Sec | Relationships / Sec | Total Load Time (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CognoDB** | 91,489 | 200,000 | 1,000 | 2,222.98 | 2,571.60 | 121.18 s |
| **Neo4j** | *not observed* | *not observed* | *not observed* | *not observed* | *not observed* | *not observed* |
| **Memgraph** | *not observed* | *not observed* | *not observed* | *not observed* | *not observed* | *not observed* |
| **FalkorDB** | *not observed* | *not observed* | *not observed* | *not observed* | *not observed* | *not observed* |

### 2. Graph Traversal Workload Latency (ms)

| Platform | 1-Hop p50 (ms) | 1-Hop p95 (ms) | 2-Hop p50 (ms) | 2-Hop p95 (ms) | 3-Hop p50 (ms) | 3-Hop p95 (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CognoDB** | 283.07 ms | 435.92 ms | 282.58 ms | 284.26 ms | 282.43 ms | 336.27 ms |
| **Neo4j** | *not observed* | *not observed* | *not observed* | *not observed* | *not observed* | *not observed* |
| **Memgraph** | *not observed* | *not observed* | *not observed* | *not observed* | *not observed* | *not observed* |
| **FalkorDB** | *not observed* | *not observed* | *not observed* | *not observed* | *not observed* | *not observed* |

### 3. Additional Workload Suite (Lookups, Aggregations, Mixed)

| Platform | Node Lookups p95 (ms) | Aggregations p95 (ms) | Mixed Read/Write p95 (ms) |
| :--- | :--- | :--- | :--- |
| **CognoDB** | *not observed* | *not observed* | *not observed* |
| **Comparison DBs** | *not observed* | *not observed* | *not observed* |

---

## 📈 Visual Performance Comparison

### Ingestion Throughput
![Data Loading Throughput](charts/load_throughput.png)

### Traversal Tail Latency (p95)
![Graph Traversal p95 Latency](charts/traversal_p95_latency.png)

---

## 🛠️ Methodology & Benchmark Setup

### Dataset Specifications
* **Dataset Name**: SNAP Pokec Online Social Network Graph
* **Source URL**: `https://snap.stanford.edu/data/soc-pokec-relationships.txt.gz`
* **License**: Public Domain / Academic Research (Stanford University)
* **Sampled Size**: 91,489 unique User nodes and 200,000 directed `FRIEND_OF` relationships
* **Referential Integrity**: 100% verified (every edge source and target exists in `nodes.csv`)

### Hardware & Environment Specs
* **Database Endpoint**: CognoDB Cloud (`bolt+s://db-996cdd46.databases.cognodb.com`)
* **Driver & Runtime**: Python 3.14.0, `neo4j` Python Driver (v6.2.0), `pandas`, `matplotlib`
* **Ingestion Strategy**: Parameterized Cypher `UNWIND` batched writes with configurable batch size (default 1,000 items per transaction)
* **Warm-up Protocol**: 15 warm-up iterations executed per workload prior to recording 100 measured iterations

---

## ⚠️ Caveats & Performance Observations

1. **Cloud Network Latency Baseline**: All CognoDB queries were executed over encrypted TLS (`bolt+s://`) against a cloud database instance. The base RTT (round-trip time) network overhead introduces a baseline network latency of ~270 ms to ~300 ms per query round-trip.
2. **Indexing Importance**: A schema index on `User(id)` was created prior to edge ingestion. Without indexing, edge link resolution requires scanning all 91,489 nodes per edge, drastically decreasing throughput.
3. **Comparison Platforms**: Additional comparison graph engines (Neo4j, Memgraph, FalkorDB) are currently listed as *not observed* until their respective platform adapters are populated in `.env` and executed.

---

## 🚀 How to Run the Benchmark

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Download & Prepare Dataset**:
   ```bash
   python data/prepare_dataset.py
   ```
3. **Run Full Benchmark Suite**:
   ```bash
   python harness/run_all.py
   ```
4. **Generate Visualization Charts**:
   ```bash
   python charts/generate_charts.py
   ```
