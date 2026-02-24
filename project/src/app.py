# Author: Gilad Bitton
# RedID: 130621085

from flask import Flask, request, jsonify
import os
import uuid
import threading
import logging
from node_manager import get_peers, get_node_id
from constants import (
    MODE_STRONG, MODE_EVENTUAL, DEFAULT_USER, DEFAULT_TIMESTAMP,
    DEFAULT_PORT, HTTP_OK, HTTP_ACCEPTED, HTTP_BAD_REQUEST, HTTP_INTERNAL_SERVER_ERROR
)
import quorum
import gossip

import random

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage
MESSAGES = []

# Configuration
MODE = os.environ.get("MODE", MODE_STRONG)  # STRONG or EVENTUAL
NODE_ID = get_node_id()
PEERS = get_peers()

# Start Gossip if in eventual mode
if MODE == MODE_EVENTUAL:
    # Initialize Gossip Protocol
    gossip_protocol = gossip.GossipProtocol(node_id=NODE_ID, peers=PEERS, storage=MESSAGES)
    gossip_protocol.start()

@app.route('/')
def health():
    return jsonify({"status": "up", "node_id": NODE_ID, "mode": MODE})

@app.route('/messages', methods=['GET'])
def get_messages():
    """Retrieve all messages."""
    return jsonify({"messages": MESSAGES, "count": len(MESSAGES)})

@app.route('/message', methods=['POST'])
def post_message():
    """
    Public endpoint for clients to post messages.
    Handles consistency logic based on MODE.
    """
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "Invalid payload"}), HTTP_BAD_REQUEST

    # Enrich message with metadata
    message = {
        "id": str(uuid.uuid4()),
        "text": data['text'],
        "user": data.get("user", DEFAULT_USER),
        "timestamp": data.get("timestamp", DEFAULT_TIMESTAMP),
        "origin_node": NODE_ID
    }

    # Total nodes
    total_nodes = len(PEERS) + 1  # including self
    majority = total_nodes // 2 + 1 # // is floor division

    # Strong Consistency (Quorum) logic
    if MODE == MODE_STRONG:
        # If the message is succesfully written to the peers, we can add it to our local storage
        result = quorum.write_message_quorum(message, PEERS)
        # Implement two cases: result is a bool or result is a bool and an int representing number of votes
        if isinstance(result, tuple) and len(result) >= 2:
            success, votes = bool(result[0]), int(result[1])
        else:
            success = bool(result)
            votes = majority if success else 1 # either majority or just oneself
        
        # In case of success, we add the message to our local node
        if success:
            # Making adding messages idempotent
            if not any(msg["id"] == message["id"] for msg in MESSAGES):
                MESSAGES.append(message)

            return jsonify({
                "status": "committed",
                "mode": "quorum",
                "replicas": votes,
                "message_id": message["id"]
            }), HTTP_OK
        return jsonify({
            "error": "write quorum failed",
            "details": f"Only {votes}/{total_nodes} nodes acknowledged the write, required {majority} for quorum."
        }), HTTP_INTERNAL_SERVER_ERROR
    # Eventual Consistency (Gossip) logic
    elif MODE == MODE_EVENTUAL:
        # Add message immediately regardless of peers
        if not any(msg["id"] == message["id"] for msg in MESSAGES):
                MESSAGES.append(message)

        return jsonify({
            "status": "accepted",
            "mode": "gossip",
            "replicas": "Propagation in progress",
            "message_id": message["id"]
        }), HTTP_ACCEPTED
    else:
        return jsonify({"error": "Unknown mode"}), HTTP_INTERNAL_SERVER_ERROR

@app.route('/internal/write', methods=['POST'])
def internal_write():
    """
    Internal endpoint used by quorum peers
    Append onlt if message id not already present; return 200 OK.
    """
    data  = request.json
    # Validate payload
    if not data or 'id' not in data:
        return jsonify({"error": "Invalid payload"}), HTTP_BAD_REQUEST
    
    incoming_message_id = data['id']
    # Check for idempotency
    if any(msg["id"] == incoming_message_id for msg in MESSAGES):
        return jsonify({"status": "ack", "note": "duplicate ignored"}), HTTP_OK

    # If not a duplicate, append to local storage
    MESSAGES.append(data)
    return jsonify({"status": "ack"}), HTTP_OK

if __name__ == '__main__':
    port = int(os.environ.get('PORT', DEFAULT_PORT))
    app.run(host='0.0.0.0', port=port, threaded=True)
