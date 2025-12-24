# Mini Dynamo Testing Guide

Complete guide to test all functionality in the Mini Dynamo project.

## Prerequisites

1. Ensure you have Python 3.9+ installed
2. Install dependencies: `pip install -r requirements.txt`
3. Open **3 separate terminal windows** for running nodes

---

## 1. Starting the Cluster

### Terminal 1 - Node 1
```bash
python node.py --port 5001
```

### Terminal 2 - Node 2
```bash
python node.py --port 5002
```

### Terminal 3 - Node 3
```bash
python node.py --port 5003
```

**Expected Output:**
```
[INFO] Node 127.0.0.1:5001 starting on port 5001
 * Running on http://0.0.0.0:5001
```

---

## 2. Basic Operations Testing

### 2.1 Write (PUT) Operations

#### Basic Write
```bash
curl -X PUT http://localhost:5001/kv/user123 \
  -H "Content-Type: application/json" \
  -d '{"value":"Alice","N":3,"W":2}'
```

**Expected Response:**
```json
{"success":true}
```

#### Write with Custom Quorum
```bash
# Write-heavy configuration (W=1, fast writes)
curl -X PUT http://localhost:5002/kv/product456 \
  -H "Content-Type: application/json" \
  -d '{"value":"Laptop","N":3,"W":1}'

# Strong consistency (W=3, all replicas must confirm)
curl -X PUT http://localhost:5003/kv/critical789 \
  -H "Content-Type: application/json" \
  -d '{"value":"Important Data","N":3,"W":3}'
```

#### Write Different Data Types
```bash
# String
curl -X PUT http://localhost:5001/kv/str_key \
  -H "Content-Type: application/json" \
  -d '{"value":"Hello World","N":3,"W":2}'

# Number
curl -X PUT http://localhost:5001/kv/num_key \
  -H "Content-Type: application/json" \
  -d '{"value":42,"N":3,"W":2}'

# Object
curl -X PUT http://localhost:5001/kv/obj_key \
  -H "Content-Type: application/json" \
  -d '{"value":{"name":"John","age":30},"N":3,"W":2}'

# Array
curl -X PUT http://localhost:5001/kv/arr_key \
  -H "Content-Type: application/json" \
  -d '{"value":[1,2,3,4,5],"N":3,"W":2}'
```

---

### 2.2 Read (GET) Operations

#### Basic Read
```bash
curl "http://localhost:5002/kv/user123?R=2"
```

**Expected Response:**
```json
{
  "versions": [
    {
      "value": "Alice",
      "vector_clock": {
        "127.0.0.1:5001": 1
      }
    }
  ]
}
```

#### Read from Different Nodes (Should Return Same Data)
```bash
# Read from node 1
curl "http://localhost:5001/kv/user123?R=2"

# Read from node 2
curl "http://localhost:5002/kv/user123?R=2"

# Read from node 3
curl "http://localhost:5003/kv/user123?R=2"
```

#### Read with Custom Quorum
```bash
# Read-heavy (R=1, fast reads)
curl "http://localhost:5001/kv/user123?R=1&N=3"

# Strong consistency (R=3, all replicas must respond)
curl "http://localhost:5001/kv/user123?R=3&N=3"
```

#### Read Non-Existent Key
```bash
curl "http://localhost:5001/kv/nonexistent?R=2"
```

**Expected Response:**
```json
{"versions": []}
```

---

### 2.3 Delete (DELETE) Operations

#### Basic Delete
```bash
curl -X DELETE http://localhost:5003/kv/user123 \
  -H "Content-Type: application/json" \
  -d '{"W":2}'
```

**Expected Response:**
```json
{"success":true}
```

#### Verify Deletion (Should Return Empty)
```bash
curl "http://localhost:5001/kv/user123?R=2"
```

**Expected Response:**
```json
{"versions": []}
```

#### Delete with Custom Quorum
```bash
curl -X DELETE http://localhost:5001/kv/product456 \
  -H "Content-Type: application/json" \
  -d '{"N":3,"W":1}'
```

---

## 3. Quorum Testing

### 3.1 Test Write Quorum (W)

#### Test W=1 (Succeeds with 1 replica)
```bash
curl -X PUT http://localhost:5001/kv/test_w1 \
  -H "Content-Type: application/json" \
  -d '{"value":"test","N":3,"W":1}'
```

#### Test W=2 (Succeeds with 2 replicas)
```bash
curl -X PUT http://localhost:5001/kv/test_w2 \
  -H "Content-Type: application/json" \
  -d '{"value":"test","N":3,"W":2}'
```

#### Test W=3 (Requires all 3 replicas)
```bash
curl -X PUT http://localhost:5001/kv/test_w3 \
  -H "Content-Type: application/json" \
  -d '{"value":"test","N":3,"W":3}'
```

### 3.2 Test Read Quorum (R)

#### Test R=1 (Fast read)
```bash
curl "http://localhost:5001/kv/test_w1?R=1&N=3"
```

#### Test R=2 (Balanced)
```bash
curl "http://localhost:5001/kv/test_w1?R=2&N=3"
```

#### Test R=3 (Strong consistency)
```bash
curl "http://localhost:5001/kv/test_w1?R=3&N=3"
```

### 3.3 Test Quorum Failure

1. **Kill one node** (e.g., kill node on port 5003)
2. **Try write with W=3** (should fail)
```bash
curl -X PUT http://localhost:5001/kv/test_fail \
  -H "Content-Type: application/json" \
  -d '{"value":"test","N":3,"W":3}'
```

**Expected Response:**
```json
{"success":false}
```

3. **Try write with W=2** (should succeed with 2 remaining nodes)
```bash
curl -X PUT http://localhost:5001/kv/test_success \
  -H "Content-Type: application/json" \
  -d '{"value":"test","N":3,"W":2}'
```

**Expected Response:**
```json
{"success":true}
```

---

## 4. Conflict Detection Testing

### 4.1 Create Concurrent Writes

**Terminal 4 - Run these commands quickly in sequence:**

```bash
# Write from node 1
curl -X PUT http://localhost:5001/kv/conflict_key \
  -H "Content-Type: application/json" \
  -d '{"value":"Version A","N":3,"W":1}'

# Write from node 2 (before first write propagates)
curl -X PUT http://localhost:5002/kv/conflict_key \
  -H "Content-Type: application/json" \
  -d '{"value":"Version B","N":3,"W":1}'
```

### 4.2 Read and Detect Conflict

```bash
curl "http://localhost:5003/kv/conflict_key?R=2"
```

**Expected Response (with conflicts):**
```json
{
  "versions": [
    {
      "value": "Version A",
      "vector_clock": {
        "127.0.0.1:5001": 1
      }
    },
    {
      "value": "Version B",
      "vector_clock": {
        "127.0.0.1:5002": 1
      }
    }
  ]
}
```

### 4.3 Resolve Conflict (Write with Merged Vector Clock)

```bash
# Write a resolved version
curl -X PUT http://localhost:5001/kv/conflict_key \
  -H "Content-Type: application/json" \
  -d '{"value":"Resolved Version","N":3,"W":2}'
```

### 4.4 Verify Conflict Resolution

```bash
curl "http://localhost:5002/kv/conflict_key?R=2"
```

**Expected Response (single version):**
```json
{
  "versions": [
    {
      "value": "Resolved Version",
      "vector_clock": {
        "127.0.0.1:5001": 2,
        "127.0.0.1:5002": 1
      }
    }
  ]
}
```

---

## 5. Read Repair Testing

### 5.1 Create Data Divergence

1. **Write to node 1 only** (with W=1)
```bash
curl -X PUT http://localhost:5001/kv/repair_test \
  -H "Content-Type: application/json" \
  -d '{"value":"Initial Data","N":3,"W":1}'
```

2. **Update on node 1** (creates newer version)
```bash
curl -X PUT http://localhost:5001/kv/repair_test \
  -H "Content-Type: application/json" \
  -d '{"value":"Updated Data","N":3,"W":1}'
```

### 5.2 Trigger Read Repair

**Read from node 2** (should trigger read repair)
```bash
curl "http://localhost:5002/kv/repair_test?R=2"
```

### 5.3 Verify Repair

**Read from node 3** (should now have updated data)
```bash
curl "http://localhost:5003/kv/repair_test?R=2"
```

**Expected:** Should return "Updated Data" after read repair propagates.

---

## 6. Failure Tolerance Testing

### 6.1 Test with One Node Down

1. **Kill node on port 5003** (Ctrl+C or `kill` command)

2. **Write with W=2** (should succeed)
```bash
curl -X PUT http://localhost:5001/kv/failure_test \
  -H "Content-Type: application/json" \
  -d '{"value":"Survives Failure","N":3,"W":2}'
```

3. **Read with R=2** (should succeed)
```bash
curl "http://localhost:5002/kv/failure_test?R=2"
```

### 6.2 Test Recovery

1. **Restart node 3**
```bash
python node.py --port 5003
```

2. **Read from node 3** (triggers read repair)
```bash
curl "http://localhost:5003/kv/failure_test?R=2"
```

3. **Verify node 3 has data**
```bash
curl "http://localhost:5003/kv/failure_test?R=1"
```

---

## 7. Metrics Testing

### 7.1 Check Metrics After Operations

```bash
# Get metrics from node 1
curl -s http://localhost:5001/metrics | jq .

# Get metrics from node 2
curl -s http://localhost:5002/metrics | jq .

# Get metrics from node 3
curl -s http://localhost:5003/metrics | jq .
```

**Expected Response:**
```json
{
  "operations": {
    "reads": 5,
    "writes": 3,
    "read_repairs": 1,
    "conflicts": 0,
    "failures": 0
  },
  "quorum_rates": {
    "read_success_rate": 1.0,
    "write_success_rate": 1.0
  },
  "latency": {
    "read": {
      "avg": 12.5,
      "min": 8.2,
      "max": 25.3,
      "p95": 22.1
    },
    "write": {
      "avg": 15.8,
      "min": 10.1,
      "max": 30.5,
      "p95": 28.2
    }
  },
  "node_health": {
    "127.0.0.1:5002": {
      "success_rate": 0.95,
      "timeout_rate": 0.05,
      "total_requests": 20
    }
  }
}
```

### 7.2 Monitor Metrics Over Time

Run multiple operations, then check metrics:
```bash
# Run 10 writes
for i in {1..10}; do
  curl -X PUT http://localhost:5001/kv/metric_test_$i \
    -H "Content-Type: application/json" \
    -d "{\"value\":\"test$i\",\"N\":3,\"W\":2}" > /dev/null 2>&1
done

# Run 10 reads
for i in {1..10}; do
  curl "http://localhost:5001/kv/metric_test_$i?R=2" > /dev/null 2>&1
done

# Check metrics
curl -s http://localhost:5001/metrics | jq '.operations'
```

---

## 8. Consistency Testing

### 8.1 Test Strong Consistency (R+W > N)

```bash
# Write with W=2
curl -X PUT http://localhost:5001/kv/consistency_test \
  -H "Content-Type: application/json" \
  -d '{"value":"Strong","N":3,"W":2}'

# Read with R=2 (R+W=4 > N=3, strong consistency)
curl "http://localhost:5002/kv/consistency_test?R=2"
```

**Expected:** Should always see the latest write.

### 8.2 Test Eventual Consistency (R+W ≤ N)

```bash
# Write with W=1
curl -X PUT http://localhost:5001/kv/eventual_test \
  -H "Content-Type: application/json" \
  -d '{"value":"Eventual","N":3,"W":1}'

# Read with R=1 (R+W=2 ≤ N=3, eventual consistency)
curl "http://localhost:5002/kv/eventual_test?R=1"
```

**Note:** May see stale data temporarily.

---

## 9. Edge Cases Testing

### 9.1 Invalid Quorum Parameters

```bash
# Invalid: R > N
curl "http://localhost:5001/kv/test?R=5&N=3"

# Invalid: W > N
curl -X PUT http://localhost:5001/kv/test \
  -H "Content-Type: application/json" \
  -d '{"value":"test","N":3,"W":5}'

# Invalid: Negative values
curl -X PUT http://localhost:5001/kv/test \
  -H "Content-Type: application/json" \
  -d '{"value":"test","N":-1,"W":2}'
```

**Expected:** Error responses with status 400

### 9.2 Empty/Missing Values

```bash
# Missing value in PUT
curl -X PUT http://localhost:5001/kv/test \
  -H "Content-Type: application/json" \
  -d '{"N":3,"W":2}'

# Empty value
curl -X PUT http://localhost:5001/kv/test \
  -H "Content-Type: application/json" \
  -d '{"value":"","N":3,"W":2}'
```

### 9.3 Large Keys/Values

```bash
# Large key
curl -X PUT "http://localhost:5001/kv/$(python3 -c 'print("x"*1000)')" \
  -H "Content-Type: application/json" \
  -d '{"value":"test","N":3,"W":2}'

# Large value
curl -X PUT http://localhost:5001/kv/large_value \
  -H "Content-Type: application/json" \
  -d "{\"value\":\"$(python3 -c 'print("x"*10000)')\",\"N\":3,\"W\":2}"
```

---

## 10. Integration Testing Script

Create a test script to run all tests:

```bash
#!/bin/bash
# save as test_all.sh

echo "=== Starting Integration Tests ==="

# Test 1: Basic Write
echo "Test 1: Basic Write"
curl -X PUT http://localhost:5001/kv/integration_test \
  -H "Content-Type: application/json" \
  -d '{"value":"test","N":3,"W":2}'

# Test 2: Basic Read
echo "Test 2: Basic Read"
curl "http://localhost:5002/kv/integration_test?R=2"

# Test 3: Update
echo "Test 3: Update"
curl -X PUT http://localhost:5001/kv/integration_test \
  -H "Content-Type: application/json" \
  -d '{"value":"updated","N":3,"W":2}'

# Test 4: Read After Update
echo "Test 4: Read After Update"
curl "http://localhost:5003/kv/integration_test?R=2"

# Test 5: Delete
echo "Test 5: Delete"
curl -X DELETE http://localhost:5001/kv/integration_test \
  -H "Content-Type: application/json" \
  -d '{"W":2}'

# Test 6: Read After Delete
echo "Test 6: Read After Delete"
curl "http://localhost:5002/kv/integration_test?R=2"

# Test 7: Metrics
echo "Test 7: Metrics"
curl -s http://localhost:5001/metrics | jq '.operations'

echo "=== Tests Complete ==="
```

**Run the script:**
```bash
chmod +x test_all.sh
./test_all.sh
```

---

## 11. Performance Testing

### 11.1 Load Testing

```bash
# Write 100 keys
for i in {1..100}; do
  curl -X PUT http://localhost:5001/kv/load_test_$i \
    -H "Content-Type: application/json" \
    -d "{\"value\":\"data$i\",\"N\":3,\"W\":2}" > /dev/null 2>&1
done

# Read 100 keys
for i in {1..100}; do
  curl "http://localhost:5001/kv/load_test_$i?R=2" > /dev/null 2>&1
done

# Check metrics
curl -s http://localhost:5001/metrics | jq '.latency'
```

### 11.2 Concurrent Requests

```bash
# Run 10 concurrent writes
for i in {1..10}; do
  curl -X PUT http://localhost:5001/kv/concurrent_$i \
    -H "Content-Type: application/json" \
    -d "{\"value\":\"concurrent$i\",\"N\":3,\"W\":1}" &
done
wait

# Check for conflicts
curl "http://localhost:5001/kv/concurrent_5?R=2"
```

---

## 12. Quick Reference

### Common Test Scenarios

| Scenario | Command |
|----------|---------|
| Basic write | `curl -X PUT http://localhost:5001/kv/key -H "Content-Type: application/json" -d '{"value":"data","N":3,"W":2}'` |
| Basic read | `curl "http://localhost:5001/kv/key?R=2"` |
| Delete | `curl -X DELETE http://localhost:5001/kv/key -H "Content-Type: application/json" -d '{"W":2}'` |
| Metrics | `curl -s http://localhost:5001/metrics \| jq .` |
| Strong consistency | `R=2, W=2, N=3` |
| Eventual consistency | `R=1, W=1, N=3` |
| Write-heavy | `R=3, W=1, N=3` |
| Read-heavy | `R=1, W=3, N=3` |

---

## Troubleshooting

### Node won't start
- Check if port is already in use: `lsof -i :5001`
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Quorum failures
- Verify all 3 nodes are running
- Check network connectivity between nodes
- Review node logs for errors

### Conflicts not detected
- Ensure writes happen concurrently (within milliseconds)
- Check vector clock implementation
- Verify conflict resolution logic

### Metrics showing zeros
- Ensure operations have been performed
- Check metrics collection is enabled
- Verify metrics endpoint is accessible

---

## Next Steps

After running these tests, you should have verified:
- ✅ Basic CRUD operations
- ✅ Quorum enforcement
- ✅ Conflict detection and resolution
- ✅ Read repair functionality
- ✅ Failure tolerance
- ✅ Metrics collection
- ✅ Consistency guarantees

For production use, consider adding:
- Automated test suite (pytest)
- Load testing tools (Apache Bench, wrk)
- Monitoring dashboards
- Alerting on failures

