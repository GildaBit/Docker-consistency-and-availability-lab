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
- **Docker Version:** [output of `docker --version`]
- **Python Version:** [output of `python3 --version`]

## 2. Response Time Comparison

> Run `python3 benchmark_tool.py --mode quorum` and `python3 benchmark_tool.py --mode gossip` 
> to collect these measurements automatically.

### Quorum Mode (Strong Consistency)
| Test | Response Time (ms) | Status Code |
|------|-------------------|-------------|
| Single message POST | [e.g., 45] | 200 |
| 5 concurrent POSTs (avg) | [e.g., 78] | 200 |

### Gossip Mode (Eventual Consistency)
| Test | Response Time (ms) | Status Code |
|------|-------------------|-------------|
| Single message POST | [e.g., 12] | 202 |
| 5 concurrent POSTs (avg) | [e.g., 15] | 202 |

## 3. Convergence Test (Gossip Mode)
- **Time for message to appear on all nodes:** [e.g., 4.2 seconds]
- **Number of gossip rounds observed:** [e.g., 2]

## 4. Partition Test

Test the same scenario in BOTH modes to observe the CAP trade-off:

### Scenario: Kill 2 of 3 nodes, then attempt a write

| Mode | Command | Status Code | Behavior |
|------|---------|-------------|----------|
| Quorum (STRONG) | `curl -X POST localhost:5001/message ...` | [e.g., 500] | [Describe] |
| Gossip (EVENTUAL) | `curl -X POST localhost:5001/message ...` | [e.g., 202] | [Describe] |

### Observations
- **Quorum behavior during partition:** [Did it reject the request? Why?]
- **Gossip behavior during partition:** [Did it accept the request? What are the risks?]

## 5. CAP Theorem Analysis

### Which CAP properties does each mode prioritize?
| Mode | CAP Choice | Explanation |
|------|------------|-------------|
| Quorum | [CP / AP / CA] | [Why? What does it sacrifice?] |
| Gossip | [CP / AP / CA] | [Why? What does it sacrifice?] |

### Why can't we have all three (CAP)?
[Your explanation - What makes it impossible to guarantee C, A, and P simultaneously?]

### Real-World Trade-off Scenarios
Answer: Which mode would you choose for each scenario, and why?

1. **Bank account balance:** [Quorum/Gossip] because [reason]
2. **Social media "likes" counter:** [Quorum/Gossip] because [reason]
3. **Airline seat reservation:** [Quorum/Gossip] because [reason]
4. **User online/offline status:** [Quorum/Gossip] because [reason]

## 6. Performance Observations

### Why is Quorum slower?
[Your explanation - e.g., "Quorum must wait for network round-trips to 2 other nodes before responding..."]

### Why is Gossip faster but temporarily inconsistent?
[Your explanation - e.g., "Gossip returns immediately after local write. The propagation delay means..."]

## 7. Testing Commands Used
```bash
# Example commands you ran
curl -X POST http://localhost:5001/message -H "Content-Type: application/json" -d '{"text":"test","user":"alice"}'
curl http://localhost:5002/messages
```
