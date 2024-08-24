from interactive_gym.scenes import scene


class Stager:
    """
    The Stager class is used to stage a sequence of Scenes for a participant to interact with.

    The design is inspired by nodeGame (Balietti, 2017).
    """

    def __init__(self, scenes: list[scene.Scene], **kwargs):
        """
        Initialize the Stager with a list of Scenes.

        Args:
            scenes (List[Scene]): A list of Scenes to stage.
        """
        self.scenes = scenes
        self.current_scene_index = 0
        self.current_scene = self.scenes[self.current_scene_index]
        self.kwargs = kwargs

    def next(self):
        """
        Move to the next Scene in the sequence.
        """
        self.current_scene_index += 1
        if self.current_scene_index >= len(self.scenes):
            return None
        self.current_scene = self.scenes[self.current_scene_index]
        return self.current_scene
