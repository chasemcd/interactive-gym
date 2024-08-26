from __future__ import annotations

import copy
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

    def __init__(self, scene_id: str, **kwargs):
        self.scene_id = scene_id
        self.sio: flask_socketio.SocketIO | None = None
        self.status = SceneStatus.Inactive

    def build(self, sio: flask_socketio.SocketIO) -> Scene:
        """
        Build the Scene.
        """
        return copy.deepcopy(self)

    def unpack(self) -> list[Scene]:
        """
        Unpack a scene, in the base class this just returns the scene in a list.
        """
        return [self]

    def activate(self, sio: flask_socketio.SocketIO):
        """
        Activate the current scene.
        """
        self.sio = sio
        self.status = SceneStatus.Active
        self.sio.emit("activate_scene", {"scene": self.scene_metadata()})

    def deactivate(self):
        """
        Deactivate the current scene.
        """
        self.status = SceneStatus.Done
        self.sio.emit("deactivate_scene", {"status": self.status})

    @property
    def scene_metadata(self) -> dict:
        """
        Return the metadata for the current scene that will be passed through the Flask app.
        """
        return {
            "scene_id": self.scene_id,
            "scene_type": self.__class__.__name__,
        }


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
