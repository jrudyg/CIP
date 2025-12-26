import logging
import time

logger = logging.getLogger(__name__)

class RealSSEClient:
    def __init__(self, session_id):
        self.session_id = session_id
        self.state = "INIT"
        self._event_count = 0

    def connect(self):
        self.state = "ACTIVE"

    def disconnect(self):
        self.state = "TERMINATED"

    def get_state(self):
        return self.state

    def get_next_event(self):
        self._event_count += 1
        if self._event_count % 5 == 0: # Log every 5 events as a keepalive
            logger.info(f"{{''event'': ''keepalive'', ''source'': ''RealSSEClient'', ''event_count'': {self._event_count}}}")
        
        time.sleep(0.2) # Reduced sleep time for faster testing
        return {"event": "real_event", "data": "some data", "id": str(self._event_count)}
