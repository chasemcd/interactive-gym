from interactive_gym.scenes import scene
from interactive_gym.configurations import remote_config


class GymScene(scene.Scene):
    """GymScene is a Scene that represents an interaction with a Gym-style environment.

    All gym scenes begin with a static HTML page that loads the necessary assets and initializes the environment.
    Participants then click the "Start" button to begin interaction with the scene.

    """

    def __init__(self, remote_game_config: remote_config.RemoteConfig):
        self.remote_game_config: remote_config.RemoteConfig = remote_game_config
