# Canary Evidence: S2.T4 Frontend SSE Client Selection

- **Date:** 2025-12-14
- **Canary Scope:** Frontend SSE client selection via feature flag.
- **Flag:** `FLAG_ENABLE_LIVE_P7_STREAM` (Default: `OFF`)

---

## PERMANENT EVIDENCE BLOCK

This log excerpt proves the frontend bridge correctly selects the `MockSSEClient` or `RealSSEClient` based on the feature flag''s boolean state. It also demonstrates keepalive logging emitted directly by the `RealSSEClient` when active.

### ---PHASE 1 (OFF)---
2025-12-14 14:21:54,502 - frontend.workspace.workspace_sse_bridge - {''event'': ''flag_check'', ''flag_key'': ''FLAG_ENABLE_LIVE_P7_STREAM'', ''flag_value'': false}
2025-12-14 14:21:54,502 - frontend.workspace.workspace_sse_bridge - {''event'': ''client_selected'', ''client'': ''MockSSEClient''}

### ---PHASE 2 (ON)---
2025-12-14 14:22:00,507 - frontend.workspace.workspace_sse_bridge - {''event'': ''flag_check'', ''flag_key'': ''FLAG_ENABLE_LIVE_P7_STREAM'', ''flag_value'': true}
2025-12-14 14:22:00,507 - frontend.workspace.workspace_sse_bridge - {''event'': ''client_selected'', ''client'': ''RealSSEClient''}
2025-12-14 14:22:00,507 - frontend.workspace.workspace_sse_bridge - {''event'': ''connection_state'', ''old_state'': ''INITIALIZED'', ''new_state'': ''ACTIVE''}
2025-12-14 14:22:01,308 - frontend.clients.real_sse_client - {''event'': ''keepalive'', ''source'': ''RealSSEClient'', ''event_count'': 5}

### ---PHASE 3 (ROLLBACK OFF)---
2025-12-14 14:22:01,710 - frontend.workspace.workspace_sse_bridge - {''event'': ''flag_check'', ''flag_key'': ''FLAG_ENABLE_LIVE_P7_STREAM'', ''flag_value'': false}
2025-12-14 14:22:01,710 - frontend.workspace.workspace_sse_bridge - {''event'': ''client_selected'', ''client'': ''MockSSEClient''}
