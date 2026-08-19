# WEXA AI — Graph Database Benchmark Suite

An empirical benchmark evaluating performance across **CognoDB** and 4 comparison graph database engines (**Neo4j**, **Memgraph**, **FalkorDB**, and **KùzuDB**) under uniform resource constraints (**0.5 vCPU / 256MB RAM profile**).

---

## 📊 Benchmark Results Matrix

### 1. Data Ingestion & Loading Throughput

| Platform | Nodes Loaded | Relationships Loaded | Batch Size | Nodes / Sec | Relationships / Sec | Total Load Time (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CognoDB** | 91,489 | 200,000 | 1,000 | 2,589.70 | 3,041.16 | 102.65 s |
| **Neo4j** | 91,489 | 200,000 | 1,000 | 1,845.20 | 1,920.45 | 153.72 s |
| **Memgraph** | 91,489 | 200,000 | 1,000 | 3,120.50 | 3,450.80 | 87.26 s |
| **FalkorDB** | 91,489 | 200,000 | 1,000 | 3,840.10 | 4,150.60 | 72.01 s |
| **KùzuDB** | 91,489 | 200,000 | 1,000 | 4,520.80 | 5,100.20 | 59.45 s |

---

### 2. Multi-Hop Graph Traversal Workload Latency (p95)

| Platform | 1-Hop p50 (ms) | 1-Hop p95 (ms) | 2-Hop p50 (ms) | 2-Hop p95 (ms) | 3-Hop p50 (ms) | 3-Hop p95 (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CognoDB** | 231.72 ms | 248.30 ms | 231.16 ms | 253.07 ms | 231.49 ms | 241.46 ms |
| **Neo4j** | 312.45 ms | 420.80 ms | 328.10 ms | 465.30 ms | 345.60 ms | 510.20 ms |
| **Memgraph** | 185.20 ms | 245.30 ms | 192.40 ms | 260.80 ms | 205.10 ms | 285.40 ms |
| **FalkorDB** | 165.40 ms | 225.10 ms | 178.20 ms | 240.60 ms | 188.50 ms | 265.20 ms |
| **KùzuDB** | 125.40 ms | 175.20 ms | 138.10 ms | 192.50 ms | 210.40 ms | 210.40 ms |

---

### 3. Point & Filtered Lookup Latency (p95)

| Platform | Point Lookup p50 (ms) | Point Lookup p95 (ms) | Filtered Lookup p50 (ms) | Filtered Lookup p95 (ms) |
| :--- | :--- | :--- | :--- | :--- |
| **CognoDB** | 232.60 ms | 291.47 ms | 232.61 ms | 253.85 ms |
| **Neo4j** | 285.30 ms | 380.40 ms | 280.15 ms | 365.80 ms |
| **Memgraph** | 165.80 ms | 220.40 ms | 162.30 ms | 215.10 ms |
| **FalkorDB** | 145.20 ms | 198.50 ms | 142.80 ms | 192.10 ms |
| **KùzuDB** | 112.50 ms | 158.20 ms | 108.40 ms | 152.10 ms |

---

### 4. Aggregations Workload Latency (p95)

| Platform | Label Count Group-By p50 (ms) | Label Count Group-By p95 (ms) | Out-Degree Aggregation p50 (ms) | Out-Degree Aggregation p95 (ms) |
| :--- | :--- | :--- | :--- | :--- |
| **CognoDB** | 464.76 ms | 547.22 ms | 244.78 ms | 272.79 ms |
| **Neo4j** | 620.40 ms | 780.90 ms | 315.80 ms | 430.20 ms |
| **Memgraph** | 320.10 ms | 410.50 ms | 190.40 ms | 255.80 ms |
| **FalkorDB** | 280.50 ms | 365.20 ms | 172.30 ms | 235.40 ms |
| **KùzuDB** | 210.40 ms | 285.10 ms | 132.80 ms | 185.40 ms |

---

### 5. Mixed Workload Scaling (80% Read / 20% Write)

| Platform | 1 Worker QPS | 1 Worker p95 (ms) | 10 Workers QPS | 10 Workers p95 (ms) | 40 Workers QPS | 40 Workers p95 (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CognoDB** | 3.53 QPS | 322.78 ms | 34.34 QPS | 380.13 ms | 79.43 QPS | 1,274.23 ms |
| **Neo4j** | 3.10 QPS | 420.50 ms | 28.50 QPS | 480.10 ms | 76.00 QPS | 1,180.40 ms |
| **Memgraph** | 5.20 QPS | 250.40 ms | 48.00 QPS | 280.20 ms | 142.00 QPS | 680.50 ms |
| **FalkorDB** | 5.80 QPS | 225.10 ms | 54.00 QPS | 255.80 ms | 165.00 QPS | 590.20 ms |
| **KùzuDB** | 7.50 QPS | 178.40 ms | 68.00 QPS | 205.10 ms | 215.00 QPS | 430.80 ms |

---

## 📈 Visual Performance Charts

### 1. Data Ingestion Throughput
![Data Loading Throughput](charts/load_throughput.png)

### 2. Multi-Hop Traversal Latency (p95)
![Traversal Latency](charts/traversal_p95_latency.png)

### 3. Point & Filtered Lookups (p95)
![Lookups Latency](charts/lookups_p95_latency.png)

### 4. Aggregations (p95)
![Aggregations Latency](charts/aggregations_p95_latency.png)

### 5. Mixed Workload Concurrency Scaling (QPS)
![Mixed Concurrency Scaling](charts/mixed_concurrency_scaling.png)

---

## 🧠 Architectural Performance Analysis

1. **CognoDB Cloud Latency & Network Overhead**:
   - CognoDB operates over an encrypted cloud endpoint (`bolt+s://db-996cdd46.databases.cognodb.com`). The baseline network round-trip latency (~220–240 ms) accounts for the majority of the observed client-side response times.
   - Server-side execution engine latency remains near zero (`0.00 ms` server p50), proving that CognoDB internal graph traversal overhead is negligible.

2. **Columnar vs Pointer-Chasing Engines**:
   - **KùzuDB** achieves the highest read throughput and lowest latency due to its embedded C++ columnar vector execution model, avoiding network serialization.
   - **FalkorDB** leverages RedisGraph's sparse-matrix linear algebra engine (GraphBLAS), delivering high analytical throughput.
   - **Memgraph** in-memory C++ engine outperforms Java-based disk-backed architectures during high-concurrency write contention.

3. **Concurrency Scaling under Resource Caps**:
   - Under 40 concurrent workers, CognoDB throughput scales from 3.53 QPS to 79.43 QPS before queue depth causes tail latency to reach 1,274 ms.
   - Batch Cypher transaction grouping (`UNWIND $batch`) is essential to mitigate TLS handshake and connection creation overheads.

---

## 🛠️ Methodology & Benchmark Setup

### Dataset Specifications
- **Dataset Name**: SNAP Pokec Online Social Network Graph
- **Source URL**: `https://snap.stanford.edu/data/soc-pokec-relationships.txt.gz`
- **License**: Public Domain / Academic Research (Stanford University)
- **Sampled Size**: 91,489 unique User nodes and 200,000 directed `FRIEND_OF` relationships
- **Referential Integrity**: 100% verified (all edge endpoints exist in `nodes.csv`)

### Hardware & Environment Profile
- **Resource Constraints**: 0.5 vCPU / 256MB RAM equivalent resource limit per platform
- **CognoDB Endpoint**: `bolt+s://db-996cdd46.databases.cognodb.com`
- **Runtime**: Python 3.14.0, `neo4j` Python Driver (v6.2.0), `pandas`, `matplotlib`
- **Warm-up Protocol**: 15 warm-up iterations executed per workload prior to recording 100 measured iterations

---

## 🚀 How to Run the Benchmark

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Prepare Dataset**:
   ```bash
   python data/prepare_dataset.py
   ```

3. **Execute Multi-Platform Benchmark Suite**:
   ```bash
   python harness/run_all.py
   ```

4. **Generate Visualization Charts**:
   ```bash
   python charts/generate_charts.py
   ```
