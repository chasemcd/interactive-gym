from __future__ import annotations

import copy
import json
import random

import flask_socketio


class SceneStatus:
    Inactive = 0
    Active = 1
    Done = 2


class Scene:
    """
    An Interactive Gym Scene defines an stage of interaction that a participant will have with the application.
    """

    def __init__(self, scene_id: str, ig_config: dict, **kwargs):
        self.scene_id = scene_id
        self.ig_config = ig_config
        self.sio: flask_socketio.SocketIO | None = None
        self.status = SceneStatus.Inactive

    def build(self) -> list[Scene]:
        """
        Build the Scene.
        """
        scene_copy = copy.deepcopy(self)
        return [scene_copy]

    def unpack(self) -> list[Scene]:
        """
        Unpack a scene, in the base class this just returns the scene in a list.
        """
        return [self]

    def activate(self, sio: flask_socketio.SocketIO):
        """
        Activate the current scene.
        """
        self.status = SceneStatus.Active
        self.sio = sio
        self.sio.emit("activate_scene", {**self.scene_metadata})

    def deactivate(self):
        """
        Deactivate the current scene.
        """
        self.status = SceneStatus.Done
        self.sio.emit("terminate_scene", {**self.scene_metadata})

    @property
    def scene_metadata(self) -> dict:
        """
        Return the metadata for the current scene that will be passed through the Flask app.
        """
        return {
            "scene_id": self.scene_id,
            "scene_type": self.__class__.__name__,
        }

    @property
    def scene_metadata(self) -> dict:
        """
        Return the metadata for the current scene that will be passed through the Flask app.
        """
        vv = serialize_dict(vars(self))
        metadata = copy.deepcopy(vv)
        return {
            "scene_id": self.scene_id,
            "scene_type": self.__class__.__name__,
            **metadata,
        }


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


class SceneWrapper:
    """
    The SceneWrapper class is used to wrap a Scene(s) with additional functionality.
    """

    def __init__(self, scenes: Scene | SceneWrapper | list[Scene], **kwargs):

        if isinstance(scenes, Scene):
            scenes = [scenes]

        self.scenes: Scene | SceneWrapper = scenes

    def build(self) -> SceneWrapper:
        """
        Build the SceneWrapper for a participant.
        """

        scenes = []
        for scene in self.unpack():
            scenes.append(scene.build())

        return scenes

    def unpack(self) -> list[Scene]:
        """
        Recursively unpack all scenes from this wrapper.
        """
        unpacked_scenes = []
        for scene in self.scenes:
            unpacked_scene = scene.unpack()
            unpacked_scenes.extend(unpacked_scene)
        return unpacked_scenes


class RandomizeOrder(SceneWrapper):
    """Randomize the order of the Scenes in the sequence."""

    def __init__(
        self,
        scenes: Scene | SceneWrapper | list[Scene],
        seed: int | None = None,
        **kwargs,
    ):
        super().__init__(scenes, **kwargs)

    def buld(self) -> RandomizeOrder:
        """
        Randomize the order before building the SceneWrapper.
        """
        random.shuffle(self.scenes)
        return super().build()
