class MockSSEClient:
    def __init__(self, session_id):
        self.session_id = session_id
        self.state = "INIT"
    def connect(self):
        self.state = "ACTIVE"
    def disconnect(self):
        self.state = "TERMINATED"
    def get_state(self):
        return self.state
    def get_next_event(self):
        import time
        time.sleep(1)
        return {"event": "mock_event", "data": "some mock data", "id": "456"}

