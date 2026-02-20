.PHONY: run run-quorum run-gossip stop clean lint benchmark-quorum benchmark-gossip

# Default target
all: run-quorum

# Run the cluster in STRONG consistency mode (Quorum)
run: run-quorum

run-quorum:
	@echo "Starting cluster in QUORUM mode (Strong Consistency)..."
	docker compose up -d --build

# Run the cluster in EVENTUAL consistency mode (Gossip)
run-gossip:
	@echo "Starting cluster in GOSSIP mode (Eventual Consistency)..."
	docker compose -f docker-compose.eventual.yml up -d --build

# Stop the cluster
stop:
	@echo "Stopping cluster..."
	docker compose down
	docker compose -f docker-compose.eventual.yml down 2>/dev/null || true

# Benchmark performance (run while cluster is running in another terminal)
benchmark-quorum:
	@echo "Benchmarking QUORUM mode..."
	@echo "Make sure cluster is running with: make run-quorum"
	python3 benchmark_tool.py --mode quorum

benchmark-gossip:
	@echo "Benchmarking GOSSIP mode..."
	@echo "Make sure cluster is running with: make run-gossip"
	python3 benchmark_tool.py --mode gossip

# Clean up temporary files
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache

# Check for linting errors (optional)
lint:
	@echo "Running linter..."
	# pip install flake8
	# flake8 src/

