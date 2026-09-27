"""Central Platform Learning Engine Integration Package (Phase 07).

Master Plan Section 16:
Connects existing core learning intelligence (BKT, mastery, LDG, difficulty,
misconceptions, spaced review, concept selection, adaptive engine) to the
central learning event store and Authoritative Student Learning Record (SLR).
"""
from central_platform.learning.backtest import BacktestResult, FrozenHistoryBacktester
from central_platform.learning.bridge import LearningEngineBridge
from central_platform.learning.models import EngineActionResult, StudentActionPayload

__all__ = [
    "BacktestResult",
    "EngineActionResult",
    "FrozenHistoryBacktester",
    "LearningEngineBridge",
    "StudentActionPayload",
]
