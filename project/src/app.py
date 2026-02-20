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

# TODO: Start Gossip if in eventual mode
# HINT: Check if MODE is MODE_EVENTUAL and call gossip.start_gossip_thread(...)

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

    if MODE == MODE_STRONG:
        # TODO: Implement Strong Consistency (Quorum) logic
        # See prompt for guidance
        pass 

    elif MODE == MODE_EVENTUAL:
        # TODO: Implement Eventual Consistency (Gossip) logic
        # See prompt for guidance
        pass
    
    else:
        return jsonify({"error": "Unknown mode"}), HTTP_INTERNAL_SERVER_ERROR

@app.route('/internal/write', methods=['POST'])
def internal_write():
    # TODO: Implement internal endpoint for peers to accept a write (used in Quorum mode). 
    # See prompt for guidance
    pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', DEFAULT_PORT))
    app.run(host='0.0.0.0', port=port, threaded=True)
