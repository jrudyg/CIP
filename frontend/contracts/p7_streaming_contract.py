
# --- ADDITIVE REPLAY PATCH FOR V1.1 READINESS ---
class ReplayEventPayload(TypedDict):
    session_id: str
    event_data: Dict[str, Any]
    replay_segment_id: Optional[str] # Required for TASK 9 visualization

