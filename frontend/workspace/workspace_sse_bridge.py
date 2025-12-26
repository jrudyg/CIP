from typing import Dict, Any, Optional
import logging
from frontend.events.p7_event_model import P7Event
from frontend.clients.real_sse_client import RealSSEClient
from frontend.clients.mock_sse_client import MockSSEClient
from frontend.flags.s2_t4_flag_control import is_feature_enabled, get_flag_name_stream_enable

logger = logging.getLogger(__name__)

class WorkspaceSSEBridge:
    def __init__(self, session_id: str):
        self._session_id = session_id
        self._client: Optional[Any] = None
        self.last_state: Optional[str] = "INITIALIZED"

        flag_key = get_flag_name_stream_enable()
        flag_value = is_feature_enabled(flag_key)
        logger.info(f"{{''event'': ''flag_check'', ''flag_key'': ''{flag_key}'', ''flag_value'': {str(flag_value).lower()}}}")
        
        if flag_value:
            self._client = RealSSEClient(session_id=session_id)
        else:
            self._client = MockSSEClient(session_id=session_id)
        
        logger.info(f"{{''event'': ''client_selected'', ''client'': ''{self._client.__class__.__name__}''}}")

    def connect(self):
        if self._client:
            self._client.connect()
            new_state = self._client.get_state()
            if new_state != self.last_state:
                logger.info(f"{{''event'': ''connection_state'', ''old_state'': ''{self.last_state}'', ''new_state'': ''{new_state}''}}")
                self.last_state = new_state

    def disconnect(self, initiated_by: str = "client"):
        if self._client:
            logger.info(f"{{''event'': ''disconnect'', ''initiated_by'': ''{initiated_by}''}}")
            self._client.disconnect()
            new_state = "TERMINATED"
            if new_state != self.last_state:
                logger.info(f"{{''event'': ''connection_state'', ''old_state'': ''{self.last_state}'', ''new_state'': ''{new_state}''}}")
                self.last_state = new_state

    def recover(self):
        logger.info(f"{{''event'': ''recovery_attempt''}}")
        self.connect()

    def get_latest_event(self) -> Optional[P7Event]:
        if self._client:
            return self._client.get_next_event()
        return None

    def export_state(self) -> Dict[str, Any]:
        flag_key = get_flag_name_stream_enable()
        flag_value = is_feature_enabled(flag_key)
        return {
            "session_id": self._session_id,
            "client_type": self._client.__class__.__name__ if self._client else "None",
            "connection_state": self.last_state,
            "flag_key": flag_key,
            "flag_value": flag_value
        }
