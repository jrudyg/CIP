# P7 Paths Manifest

**Document ID:** CC1-P7-MANIFEST-001
**Generated:** 2025-12-09
**Author:** CC1 (Backend Mechanic)
**Phase:** P7 Alignment Mode (Pre-activation)

---

## Target Directory Status

| Target Path | Status | Action Required |
|-------------|--------|-----------------|
| `/backend/sse/` | NOT EXISTS | CREATE |
| `/backend/session_state/` | NOT EXISTS | CREATE |
| `/backend/event_log/` | NOT EXISTS | CREATE |

---

## Proposed P7 Directory Structure

```
C:/Users/jrudy/CIP/backend/
├── sse/                          [CREATE]
│   ├── __init__.py
│   ├── endpoint_handler.py       # SSE endpoint skeleton
│   ├── event_envelope.py         # Event envelope template
│   ├── sequence_generator.py     # Sequence generator interface
│   └── replay_controller.py      # Replay controller outline
│
├── session_state/                [CREATE]
│   ├── __init__.py
│   ├── state_manager.py          # Session state management
│   └── connection_tracker.py     # Active connection tracking
│
├── event_log/                    [CREATE]
│   ├── __init__.py
│   ├── event_store.py            # Event persistence
│   └── replay_buffer.py          # Replay buffer for reconnection
│
└── [existing files...]
```

---

## Existing Related Components

### Event Envelope Foundation
| File | Path | Relevance |
|------|------|-----------|
| compare_v3_monitor.py | `C:/Users/jrudy/CIP/backend/compare_v3_monitor.py` | Contains `MonitorEnvelope` dataclass - **P7 envelope template candidate** |
| stage_runner.py | `C:/Users/jrudy/CIP/backend/stage_runner.py` | Uses event_type patterns |
| compare_v3_engine.py | `C:/Users/jrudy/CIP/backend/compare_v3_engine.py` | Event emission patterns |

### Session State Foundation
| File | Path | Relevance |
|------|------|-----------|
| trust_engine.py | `C:/Users/jrudy/CIP/backend/trust_engine.py` | Contains `session_state` references |

### Event Logging Foundation
| File | Path | Relevance |
|------|------|-----------|
| compare_v3_monitor.py | `C:/Users/jrudy/CIP/backend/compare_v3_monitor.py` | JSONL event logging (`compare_v3_events.jsonl`) |
| logger_config.py | `C:/Users/jrudy/CIP/backend/logger_config.py` | Logging infrastructure |

### Existing SSE-Adjacent Code
| File | Path | Pattern Found |
|------|------|---------------|
| api.py | `C:/Users/jrudy/CIP/backend/api.py` | SSE/EventSource references |
| pattern_cache.py | `C:/Users/jrudy/CIP/backend/pattern_cache.py` | SSE references |
| embedding_cache.py | `C:/Users/jrudy/CIP/backend/embedding_cache.py` | SSE references |
| cache_metrics.py | `C:/Users/jrudy/CIP/backend/cache_metrics.py` | SSE references |

---

## Frontend Integration Points

### P7 Frontend Targets (for CC2/CC3 reference)
| Component | Path | P7 Role |
|-----------|------|---------|
| workspace_mode.py | `C:/Users/jrudy/CIP/frontend/integrations/workspace_mode.py` | EventBuffer attachment point |
| compare_v3_integration.py | `C:/Users/jrudy/CIP/frontend/integrations/compare_v3_integration.py` | SSE client integration |
| layout_diagnostics.py | `C:/Users/jrudy/CIP/frontend/integrations/layout_diagnostics.py` | Scroll/highlight routing |

### UI Component Targets (for CC2 reference)
| Component | Path | P7 Role |
|-----------|------|---------|
| system_status.py | `C:/Users/jrudy/CIP/frontend/components/system_status.py` | ConnectionStateIndicator candidate |
| topnav.py | `C:/Users/jrudy/CIP/frontend/components/topnav.py` | SSE state overlay location |

---

## Existing Event Log Location

```
C:/Users/jrudy/CIP/logs/
├── compare_v3_events.jsonl    # 14,213 bytes - existing event stream
├── cip.log                    # 1,449,768 bytes - application log
├── backend.log                # 32,647 bytes - backend operations
└── error.log                  # 37,741 bytes - error tracking
```

---

## P7 Component Mapping

| CAI Architecture Item | Proposed Backend Location | Existing Foundation |
|-----------------------|---------------------------|---------------------|
| SSE endpoint handler skeleton | `/backend/sse/endpoint_handler.py` | `api.py` (FastAPI patterns) |
| Event envelope template | `/backend/sse/event_envelope.py` | `compare_v3_monitor.py:MonitorEnvelope` |
| Sequence generator interface | `/backend/sse/sequence_generator.py` | None (new) |
| Replay controller outline | `/backend/sse/replay_controller.py` | `compare_v3_monitor.py:get_recent_events()` |

---

## Frozen Surfaces (P7 Constraints)

| Surface | File | CC1 Constraint |
|---------|------|----------------|
| TRUST | `backend/trust_engine.py` | DO NOT MODIFY |
| GEM UX Contract | Frontend UX patterns | DO NOT MODIFY |
| Z7 Monitor | Z7 monitoring system | DO NOT MODIFY |
| API Shapes | Existing API contracts | EXTEND ONLY (no breaking changes) |

---

## CC1 Readiness Status

| Check | Status |
|-------|--------|
| Target paths scanned | COMPLETE |
| Existing foundations identified | COMPLETE |
| Frozen surfaces documented | COMPLETE |
| Manifest generated | COMPLETE |

---

**CC1 Status:** READY for P7.S1

**Awaiting:** GPT authorization to create P7 directory structure
