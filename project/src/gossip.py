import time
import threading
import random
import requests
import logging
from constants import (
    GOSSIP_INTERVAL_MIN_SECONDS, GOSSIP_INTERVAL_MAX_SECONDS,
    REQUEST_TIMEOUT_SECONDS, HTTP_OK
)

logger = logging.getLogger(__name__)

class GossipProtocol:
    def __init__(self, node_id, peers, storage):
        self.node_id = node_id
        self.peers = peers
        self.storage = storage
        self.running = True

    def start(self):
        """Starts the background gossip thread."""
        thread = threading.Thread(target=self.gossip_loop, daemon=True)
        thread.start()

    def gossip_loop(self):
        logger.info("Gossip protocol started.")
        while self.running:
            # TODO: Implement Gossip Loop
            # See prompt for guidance
            pass

    def sync_with_peer(self, peer_url):
        """
        Synchronize messages with a peer node.
        
        TODO: Implement Sync Logic
                
        EDUCATIONAL NOTE - Why Production Systems Use More Sophisticated Approaches:
        
        Our simple approach: Pull ALL messages from peer, then merge.
        Problem: As data grows, transferring everything becomes expensive (O(n) bandwidth).
        
        MERKLE TREES (used by Cassandra, Dynamo, Git):
        - A tree where each leaf is a hash of a data block, and each parent is a hash
          of its children's hashes.
        - To sync: Compare root hashes. If equal, data is identical (done!).
          If different, recursively compare children to find exactly which blocks differ.
        - Benefit: O(log n) comparisons to find differences, only transfer what's needed.
        - Example: With 1 million messages, instead of transferring all 1M, we might
          only need to compare ~20 hashes and transfer the few differing messages.
        
        VECTOR CLOCKS (used by Riak, Voldemort):
        - Each node maintains a vector of logical timestamps: {node1: 5, node2: 3, node3: 7}
        - When a node writes, it increments its own counter.
        - To sync: Compare vectors to determine causal ordering.
        - Benefit: Detects conflicts (concurrent writes) vs sequential updates.
        - Example: If node1 has {A:2, B:1} and node2 has {A:1, B:2}, there's a conflict
          (both wrote independently). If node1 has {A:2, B:1} and node2 has {A:1, B:1},
          node1's version is newer (no conflict).
        
        For this assignment, we use a simple "pull all and merge by ID" strategy,
        which is correct but inefficient at scale.
        """
        pass

def start_gossip_thread(node_id, peers, storage):
    gossip = GossipProtocol(node_id, peers, storage)
    gossip.start()
    return gossip
