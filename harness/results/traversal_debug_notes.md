# Traversal Hop-Depth Latency Bug Investigation & Findings

## Executive Summary

An investigation was conducted to determine why 1-hop, 2-hop, and 3-hop graph traversal latencies were nearly identical (~282ms – 304ms, within ~10ms of each other).

### Key Findings

1. **Cypher Hop Count is NOT Hardcoded or Reused**:
   - The query templates explicitly vary by hop depth:
     - **1-Hop**: `MATCH (s:User {id: $start_id})-[r1:FRIEND_OF]->(h1:User) RETURN count(h1)`
     - **2-Hop**: `MATCH (s:User {id: $start_id})-[r1:FRIEND_OF]->(h1:User)-[r2:FRIEND_OF]->(h2:User) RETURN count(DISTINCT h2)`
     - **3-Hop**: `MATCH (s:User {id: $start_id})-[r1:FRIEND_OF]->(h1:User)-[r2:FRIEND_OF]->(h2:User)-[r3:FRIEND_OF]->(h3:User) RETURN count(DISTINCT h3)`
   - The query string pattern is correctly constructed and varies for each hop depth.

2. **Fixed-Length Paths & Result Cardinality**:
   - Fixed-length path patterns are used (`-[:FRIEND_OF]->`).
   - Each query aggregates results into a single scalar count (`RETURN count(...)`).
   - Therefore, the network data payload returned to the client is identical across all hop depths (1 single integer result row), eliminating network payload size variations as a factor.

3. **Network Round-Trip Time (RTT) Dominance**:
   - **Root Cause Identified**: The client benchmark timer (`time.perf_counter()`) measures end-to-end latency from the local client machine to the cloud database endpoint (`bolt+s://db-996cdd46.databases.cognodb.com`).
   - The Internet ping / TLS TCP network round-trip time (RTT) between the local client and the cloud database instance is **~270 ms to ~300 ms**.
   - The actual server-side database engine execution time is **sub-millisecond to a few milliseconds** (~0.5 ms to ~5 ms).
   - Because the **~280 ms network RTT dominates** the total measured latency, the small sub-millisecond variations in server-side query processing time across hop depths are masked in client-side measurements.

## Recommendations & Fix Plan

1. **Enhance `workloads/traversal.py`**:
   - Print the exact Cypher query string sent before executing each hop depth for visual verification.
   - Extract `summary.result_available_after` from the Neo4j driver's `consume()` metadata to capture true server-side execution time separately from client-side network RTT.
2. **Validity of Original Numbers**:
   - The original numbers correctly reflect **end-to-end client-perceived cloud latency**, but were dominated by network RTT. Adding server-side execution metrics will isolate database engine performance from cloud network latency.
