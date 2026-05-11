import logging
import time
from fastapi import Request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("forensic_tool")

def log_forensic_event(request: Request, items_processed: int):
    """
    Logs forensic events without recording plaintext input or hashes.
    """
    client_ip = request.client.host
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    
    logger.info(
        f"Forensic Event: Timestamp={timestamp}, IP={client_ip}, ItemsProcessed={items_processed}"
    )
