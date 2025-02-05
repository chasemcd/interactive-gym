from __future__ import annotations
import copy
import json

from interactive_gym.scenes.stager import Stager
from interactive_gym.scenes.utils import NotProvided


class ExperimentConfig:
    def __init__(self):

        # Experiment
        self.experiment_id: str = None
        self.stager: Stager = None

        # Hosting
        self.host = None
        self.port = 8000
        self.max_ping = 100000
        self.min_ping_measurements = 5

        # Experiment data
        self.save_experiment_data = True

    def experiment(
        self,
        experiment_id: str = NotProvided,
        stager: Stager = NotProvided,
        save_experiment_data: bool = True,
    ) -> ExperimentConfig:
        if experiment_id is not NotProvided:
            self.experiment_id = experiment_id

        if stager is not NotProvided:
            self.stager = stager

        if save_experiment_data is not NotProvided:
            self.save_experiment_data = save_experiment_data

        return self

    def hosting(
        self,
        host: str | None = NotProvided,
        port: int | None = NotProvided,
        max_ping: int = NotProvided,
    ):
        if host is not NotProvided:
            self.host = host

        if port is not NotProvided:
            self.port = port

        if max_ping is not NotProvided:
            self.max_ping = max_ping

        return self

    def to_dict(self, serializable=False):
        config = copy.deepcopy(vars(self))
        if serializable:
            config = serialize_dict(config)
        return config


def serialize_dict(data):
    """
    Serialize a dictionary to JSON, removing unserializable keys recursively.

    :param data: Dictionary to serialize.
    :return: Serialized object with unserializable elements removed.
    """
    if isinstance(data, dict):
        # Use dictionary comprehension to process each key-value pair
        return {
            key: serialize_dict(value)
            for key, value in data.items()
            if is_json_serializable(value)
        }
    elif isinstance(data, list):
        # Use list comprehension to process each item
        return [
            serialize_dict(item) for item in data if is_json_serializable(item)
        ]
    elif is_json_serializable(data):
        return data
    else:
        return None  # or some other default value


def is_json_serializable(value):
    """
    Check if a value is JSON serializable.

    :param value: The value to check.
    :return: True if the value is JSON serializable, False otherwise.
    """
    try:
        json.dumps(value)
        return True
    except (TypeError, OverflowError):
        return False
