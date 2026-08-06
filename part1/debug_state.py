# ============================================================================
# debug_state.py
# Purpose
#   Global debug flag that can be toggled by F1 key.
#   Entities import this to check if debug mode is enabled.
#   Also holds a live FSM transition log for the debug overlay.
# ============================================================================

# Global debug toggle flag
DEBUG = False

# Live FSM transition log — list of (time_str, kind, index, old_state, new_state)
TRANSITION_LOG = []
MAX_LOG_ENTRIES = 10

def log_transition(kind, index, old_state, new_state):
    """Record a state transition to the live debug log."""
    import time as _time
    TRANSITION_LOG.append((_time.strftime("%H:%M:%S"), kind, index, old_state, new_state))
    if len(TRANSITION_LOG) > MAX_LOG_ENTRIES:
        TRANSITION_LOG.pop(0)
