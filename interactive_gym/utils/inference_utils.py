from __future__ import annotations

import numpy as np
from scipy import special


def sample_action_via_softmax(logits: np.ndarray) -> int:
    """Given logits sample an action via softmax"""
    action_distribution = special.softmax(logits)
    action = np.random.choice(
        np.arange(len(action_distribution)), p=action_distribution
    )
    return action
