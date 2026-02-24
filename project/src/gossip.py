# Author: Gilad Bitton
# RedID: 130621085

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
        """
        Main loop for the gossip protocol. Periodically selects a random peer and syncs messages.
        """
        logger.info("Gossip protocol started.")
        while self.running:
            # Random sleep within bounds
            sleep_time = random.uniform(
                GOSSIP_INTERVAL_MIN_SECONDS,
                GOSSIP_INTERVAL_MAX_SECONDS
            )
            time.sleep(sleep_time)

            # If no peers, skip
            if not self.peers:
                continue
            
            # Pick a random peer to gossip with
            peer_url = random.choice(self.peers)

            # Sync with the peer
            try:
                self.sync_with_peer(peer_url)
            except Exception as e:
                logger.warning(f"Gossip sync failed with {peer_url}: {e}")


    def sync_with_peer(self, peer_url):
        """
        Synchronize messages with a peer node.
        
        For this assignment, we use a simple "pull all and merge by ID" strategy,
        which is correct but inefficient at scale.
        """
        try:
            # Get messages from peer
            response = requests.get(
                f"{peer_url}/messages",
                timeout=REQUEST_TIMEOUT_SECONDS
            )

            # If did not get HTTP_OK, treat as failure
            if response.status_code != HTTP_OK:
                return
            
            peer_data = response.json()
            peer_messages = peer_data.get("messages", [])

            # Make set of all local message IDs for quick lookup
            local_ids = {msg["id"] for msg in self.storage}

            # Merge messages that are not already in local storage
            new_messages = 0
            for msg in peer_messages:
                if msg["id"] not in local_ids:
                    self.storage.append(msg)
                    local_ids.add(msg["id"])
                    new_messages += 1
            if new_messages > 0:
                logger.info(
                    f"Gossip merged {new_messages} messages from {peer_url}"
                )
        except requests.exceptions.RequestException:
            # Ignore network errors for gossip (eventual consistency tolerates failures)
            return

def start_gossip_thread(node_id, peers, storage):
    gossip = GossipProtocol(node_id, peers, storage)
    gossip.start()
    return gossip
