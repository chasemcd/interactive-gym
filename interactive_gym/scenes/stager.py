import logging
import copy
import flask_socketio

from interactive_gym.scenes import scene, static_scene


logger = logging.getLogger(__name__)


class Stager:
    """
    The Stager class is used to stage a sequence of Scenes for a participant to interact with.

    The design is inspired by the stager in nodeGame (Balietti, 2017).
    """

    def __init__(self, scenes: list[scene.Scene], **kwargs):
        """
        Initialize the Stager with a list of Scenes.

        Args:
            scenes (List[Scene]): A list of Scenes to stage.
        """

        assert isinstance(
            scenes[0], static_scene.StartScene
        ), "The first Scene in the Stager must be a StartScene."

        assert isinstance(
            scenes[-1], static_scene.EndScene
        ), "The last Scene in the Stager must be an EndScene."

        # Upack the scenes from SceneWrapper objects
        self.scenes = scenes

        self.current_scene_index = 0
        self.current_scene = self.scenes[self.current_scene_index]
        self.kwargs = kwargs

    def build_instance(
        self,
    ):
        """
        Build the Stager by activating the first Scene in the sequence.
        """
        participant_copy = copy.deepcopy(self)

        built_scenes = [s.build() for s in participant_copy.scenes]
        flattened_scenes = [
            s for scene_list in built_scenes for s in scene_list
        ]
        participant_copy.set_scenes(flattened_scenes)

        return participant_copy

    def on_connect(self, sio: flask_socketio.SocketIO, room: str | int):
        """
        A hook that is called when the client's stager is built (they're connected to the server).
        """
        for scene in self.scenes:
            scene.on_connect(sio, room)

    def get_current_scene(self) -> scene.Scene:
        return self.current_scene

    def set_scenes(self, scenes: list[scene.Scene]):
        """
        Set the scenes for the Stager.
        """
        self.scenes = scenes

    def start(self, sio: flask_socketio.SocketIO, room: str | int):
        """
        Initialize the Stager by activating the first Scene in the sequence.
        """
        assert self.current_scene_index == 0, "The Stager has already started."
        assert isinstance(
            self.current_scene, static_scene.StartScene
        ), f"start() was called with a current_scene other than StartScene. Got {type(self.current_scene)}."
        self.current_scene.activate(sio, room)
        self.on_connect(sio, room)

    def advance(self, sio: flask_socketio.SocketIO, room: str | int):
        """
        Move to the next Scene in the sequence.
        """
        self.current_scene.deactivate()
        self.current_scene_index += 1
        if self.current_scene_index >= len(self.scenes):
            logger.info("End of Stager sequence, no more scenes to stage.")
            return None

        self.current_scene = self.scenes[self.current_scene_index]
        self.current_scene.activate(sio=sio, room=room)
