# Author: Gilad Bitton
# RedID: 130621085
# Analysis: Quorum vs Gossip Performance

> **Instructions:** Copy this template to your submission as `ANALYSIS.md` and fill in all sections.
> Replace all `[bracketed text]` with your actual observations and measurements.
>
> **Tip:** Use the benchmark tool to automate measurements:
> ```bash
> python3 benchmark_tool.py --mode quorum   # While cluster runs in Quorum mode
> python3 benchmark_tool.py --mode gossip   # While cluster runs in Gossip mode
> ```
> The tool outputs results in a format you can paste directly into Section 2.

## 1. Test Environment
- **OS:** [e.g., Windows 11 / macOS 14 / Ubuntu 22.04]
- **Docker Version:** Docker version 29.1.5, build 0e6fee6
- **Python Version:** Python 3.12.3

## 2. Response Time Comparison

> Run `python3 benchmark_tool.py --mode quorum` and `python3 benchmark_tool.py --mode gossip` 
> to collect these measurements automatically.

### Quorum Mode (Strong Consistency)
| Test | Response Time (ms) | Status Code |
|------|-------------------|-------------|
| Single message POST | 8.04 ms | 200 |
| 5 concurrent POSTs (avg) | 21.52 ms | 200 |

### Gossip Mode (Eventual Consistency)
| Test | Response Time (ms) | Status Code |
|------|-------------------|-------------|
| Single message POST | 3.93 ms | 202 |
| 5 concurrent POSTs (avg) | 9.01 ms | 202 |

## 3. Convergence Test (Gossip Mode)
- **Time for message to appear on all nodes:** 3594.81 ms or ~3.6 seconds
- **Number of gossip rounds observed:** 2

## 4. Partition Test

Test the same scenario in BOTH modes to observe the CAP trade-off:

### Scenario: Kill 2 of 3 nodes, then attempt a write

| Mode | Command | Status Code | Behavior |
|------|---------|-------------|----------|
| Quorum (STRONG) | `curl -i -X POST http://localhost:5001/message -H "Content-Type: application/json" -d "{\"text\":\"partition test\",\"user\":\"tester\"}"` | 500 | Only 1/3 nodes acknowledged the write, required 2 for quorum. Write quorum failed |
| Gossip (EVENTUAL) | `curl -i -X POST http://localhost:5001/message -H "Content-Type: application/json" -d "{\"text\":\"partition test\",\"user\":\"tester\"}"` | 202 | status: accepted |

### Observations
- **Quorum behavior during partition:** During quorum it rejected the message, this is because for 3 nodes, 2 are needed for a quorum. So if 2 nodes are down, the request will be rejected since a quorum cannot be reached.
- **Gossip behavior during partition:** Gossip behavior accepted the request because under this behavior requests are accepted immediately and then propogated to the other nodes. The risk of course being inconsistency between the nodes, with each one having the possibility of having different data.

## 5. CAP Theorem Analysis

### Which CAP properties does each mode prioritize?
| Mode | CAP Choice | Explanation |
|------|------------|-------------|
| Quorum | CP | For it to be a distributed system, it needs to have partition tolerance and thus cannot compromise on that. Then, consistency is also added since a majority needs to be in agreement to implement changes. This sacrifices availability, since if a majority of nodes are unavailable, the write is rejected. |
| Gossip | AP | For it to be a distributed system, it needs to have partition tolerance and thus cannot compromise on that. Then, availability is also added since each write is accepted locally. However, consistency is sacrificed since for requests to be seen immediately, it means other nodes may have not gotten them yet and made the appropriate changes, causing temporary inconsistency between the nodes until the gossip is propagated |

### Why can't we have all three (CAP)?
In a distributed system, network partitions may happen. When it occurs, it is impossible to guarantee both consistency and availability while still tolerating partitions. For it to have consistency and partition tolerance, then availability needs to be sacrificed since a write may be rejected if some nodes are down in order to maintain consistency. For it to have availability and partition tolerance, then consistency needs to be sacrificed since as writes are accepted locally, they may yet not appear on other nodes.

### Real-World Trade-off Scenarios
Answer: Which mode would you choose for each scenario, and why?

1. **Bank account balance:** Quorum because very sensitive and important information like money in an account needs to stay consistent worldwide to prevent conflicting writes, e.g. double withdrawals.
2. **Social media "likes" counter:** Gossip because high availability is more important than an exact count, can be inconsistent from node to node.
3. **Airline seat reservation:** Quorum because it needs to remain consistent in order to prevent conflicting reservations and maintain one person per seat.
4. **User online/offline status:** Gossip because it is more important for status to be available and temporarily inconsistent, as long as it shows the correct one locally.

## 6. Performance Observations

### Why is Quorum slower?
Quorum is slower than gossip since for a write to succeed it needs to be approved by a majority of nodes. So it will go to every node and only be accepted after a majority respond with an HTTP_OK, whereas in gossip mode writes are accepted locally immediately.

### Why is Gossip faster but temporarily inconsistent?
In quorum mode, you wait for other nodes to have gotten the write and respond with an HTTP_OK to accept it, but in gossip you accept it locally immediately and then propagate the write. This means a write may appear locally but not in other nodes for a bit, and thus may be temporarily inconsistent.

## 7. Testing Commands Used
```bash
# Example commands you ran
curl -X POST http://localhost:5001/message -H "Content-Type: application/json" -d '{"text":"test","user":"alice"}'
curl http://localhost:5002/messages
python3 benchmark_tool.py --mode quorum
python3 benchmark_tool.py --mode gossip
docker compose logs -f --no-color
```
