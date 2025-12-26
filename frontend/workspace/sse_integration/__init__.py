"""
P7 Workspace SSE Integration
Real SSE → Workspace Controller Binding

CC3 P7.CC3.01 - Binding Integration
Version: 1.0.0
"""

from .event_bindings import (
    SSEEventBinding,
    PanelStateBinding,
    ScrollSyncBinding,
    HighlightBinding,
    IntelligenceUpdateBinding,
)
from .flow_dispatcher import (
    WorkspaceSSEDispatcher,
    SSEFlowStage,
    FlowMapEntry,
)
from .replay_mode import (
    ReplayModeController,
    ReplayState,
)
from .failure_matrix import (
    FailureMode,
    FailureModeHandler,
    WorkspaceFailureMatrix,
)

__version__ = "1.0.0"
__phase__ = "Phase 7 - SSE Integration"
