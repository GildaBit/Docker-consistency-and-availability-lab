import os
from constants import DEFAULT_NODE_ID, HTTP_PROTOCOL_PREFIX

def get_peers():
    """
    Parses the PEERS environment variable.
    Expected format: "node1:5000,node2:5000,node3:5000"
    Returns a list of base URLs e.g., ["http://node1:5000", ...]
    """
    peers_env = os.environ.get("PEERS", "")
    if not peers_env:
        return []
    
    # In Docker, peers might be hostnames. 
    # If running locally for testing, they might be localhost:port.
    peers = [p.strip() for p in peers_env.split(",") if p.strip()]
    
    # Ensure they have http prefix
    formatted_peers = []
    for p in peers:
        if not p.startswith(HTTP_PROTOCOL_PREFIX):
            formatted_peers.append(f"{HTTP_PROTOCOL_PREFIX}://{p}")
        else:
            formatted_peers.append(p)
    return formatted_peers

def get_node_id():
    return os.environ.get("NODE_ID", DEFAULT_NODE_ID)

