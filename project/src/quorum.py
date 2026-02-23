import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from constants import REQUEST_TIMEOUT_SECONDS, HTTP_OK, COORDINATOR_INITIAL_VOTE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def write_message_quorum(message, peers):
    """
    Writes a message to the cluster using a Quorum consensus.
    
    Args:
        message (dict): The message payload.
        peers (list): List of peer URLs.
        
    Returns:
        bool: True if Quorum achieved, False otherwise.
    """
    # First calculate total nodes and quorum size
    total_nodes = len(peers) + 1  # including self
    majority = total_nodes // 2 + 1 # // is floor division

    votes = COORDINATOR_INITIAL_VOTE  # Start with 1 vote for self

    # quorum satisfied if no peers
    if not peers:
        logger.info("No peers configured, quorum achieved trivially.")
        return True, votes
    
    # fanout with ThreadPoolExecutor to send requests in parallel
    # ThreadPoolExecutor ensure concurrency rather than sequential requests
    with ThreadPoolExecutor(max_workers=len(peers)) as executor:
        # Submit write requests to all peers
        futures = {executor.submit(_send_write_request, peer, message): peer for peer in peers}

        # as_completed is a ThreadPoolExecutor utility that yields futures as they complete
        for future in as_completed(futures):
            peer = futures[future]
            ok = False
            # Get the result of the future, which is the response from the peer node
            try:
                ok = future.result()
            except Exception as e:
                logger.warning("Unexpected error from peer %s future: %s", peer, e)
                ok = False
            
            # If peer responded with HTTP_OK, count it as a vote
            if ok:
                votes += 1
                logger.info("Peer ACK from %s. votes = %d/%d", peer, votes, total_nodes)
            else:
                logger.info("Peer NACK/FAIL from %s. votes = %d/%d", peer, votes, total_nodes)
            
            # If majority reached, no need to wait on slow peers
            if votes >= majority:
                logger.info(
                    "Quorum achieved: votes=%d, majority_needed=%d, (N=%d)", 
                    votes, majority, total_nodes
                )
                # Cancel futures that have not started yet, cancel() is used for that
                for f in futures:
                    f.cancel()
                
                return True, votes
    # After all peers responded and we don't have majority -> FAIL
    logger.warning(
        "Quorum FAILED: votes=%d, majority_needed=%d, (N=%d)",
        votes, majority, total_nodes
    )
    return False, votes

# Helper function to send write request to a peer
def _send_write_request(peer_url: str, message) -> bool:
    """
    Send the message to a peer's /internal/write endpoint.
    Returns True if peer responds with HTTP_OK
    """
    try:
        response = requests.post(
            f"{peer_url}/internal/write",
            json=message,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        return response.status_code == HTTP_OK
    except requests.exceptions.Timeout:
        logger.warning("Timeout contacting peer %s", peer_url)
        return False
    except requests.exceptions.RequestException as e:
        logger.warning("Error contacting peer %s: %s", peer_url, e)
        return False
