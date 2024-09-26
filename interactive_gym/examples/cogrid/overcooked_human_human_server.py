"""
TODO(chase): This example needs to be re-written with the Stager setup.
"""

from __future__ import annotations

import eventlet

eventlet.monkey_patch()

import argparse
from datetime import datetime

from cogrid.envs import registry

from interactive_gym.configurations import (
    configuration_constants,
    remote_config,
)
from interactive_gym.examples.cogrid_overcooked import (
    overcooked_callback,
    overcooked_utils,
)
from interactive_gym.server import server_app

MoveUp = 0
MoveDown = 1
MoveLeft = 2
MoveRight = 3
PickupDrop = 4
Toggle = 5
Noop = 6


POLICY_MAPPING = {
    0: configuration_constants.PolicyTypes.Human,
    1: configuration_constants.PolicyTypes.Human,
}
