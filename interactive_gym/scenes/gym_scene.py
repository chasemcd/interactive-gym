from __future__ import annotations


from typing import Any, Callable
import copy
import json

from interactive_gym.scenes import scene
from interactive_gym.configurations import remote_config
from interactive_gym.scenes import utils as scene_utils
from interactive_gym.configurations import configuration_constants
from interactive_gym.scenes.utils import NotProvided


class GymScene(scene.Scene):
    """GymScene is a Scene that represents an interaction with a Gym-style environment.

    All gym scenes begin with a static HTML page that loads the necessary assets and initializes the environment.
    Participants then click the "Start" button to begin interaction with the scene.

    """

    def __init__(
        self,
    ):
        super().__init__()

        # Environment
        self.env_creator: Callable | None = None
        self.env_config: dict[str, Any] | None = None
        self.env_seed: int = 42

        # Policies
        self.load_policy_fn: Callable | None = None
        self.policy_inference_fn: Callable | None = None
        self.policy_mapping: dict[str, Any] = dict()
        self.available_policies: dict[str, Any] = dict()
        self.policy_configs: dict[str, Any] = dict()
        self.frame_skip: int = 4

        # gameplay
        self.num_episodes: int = 1
        self.action_mapping: dict[str, int] = dict()
        self.human_id: str | int | None = None
        self.default_action: int | str | None = None
        self.action_population_method: str = (
            configuration_constants.ActionSettings.DefaultAction
        )
        self.input_mode: str = configuration_constants.InputModes.PressedKeys
        self.game_has_composite_actions: bool = False
        self.max_ping: int | None = None
        self.min_ping_measurements: int = 5
        self.callback: None = (
            None  # TODO(chase): add callback typehint but need to avoid circular import
        )

        # Rendering
        self.env_to_state_fn: Callable | None = None
        self.preload_specs: list[dict[str, str | int | float]] | None = None
        self.hud_text_fn: Callable | None = None
        self.location_representation: str = "relative"  # "relative" or "pixels"
        self.game_width: int | None = 600
        self.game_height: int | None = 400
        self.fps: int = 10
        self.background: str = "#FFFFFF"  # white background default
        self.state_init: list = []
        self.assets_dir: str = "./static/assets/"
        self.assets_to_preload: list[str] = []
        self.animation_configs: list = []

        # user_experience
        self.scene_header: str = None
        self.scene_body: str = None
        self.waitroom_timeout_redirect_url: str = None
        self.waitroom_timeout: int = 1000
        self.game_page_html_fn: Callable = None
        self.reset_timeout: int = 3000
        self.reset_freeze_s: int = 0

        # pyodide
        self.run_through_pyodide: bool = False
        self.environment_initialization_code: str = ""
        self.packages_to_install: list[str] = []

    def environment(
        self,
        env_creator: Callable = NotProvided,
        env_config: dict[str, Any] = NotProvided,
        seed: int = NotProvided,
    ):
        if env_creator is not NotProvided:
            self.env_creator = env_creator

        if env_config is not NotProvided:
            self.env_config = env_config

        if seed is not NotProvided:
            self.seed = seed

        return self

    def rendering(
        self,
        fps: int = NotProvided,
        env_to_state_fn: Callable = NotProvided,
        preload_specs: list[dict[str, str | float | int]] = NotProvided,
        hud_text_fn: Callable = NotProvided,
        location_representation: str = NotProvided,
        game_width: int = NotProvided,
        game_height: int = NotProvided,
        background: str = NotProvided,
        state_init: list = NotProvided,
        assets_dir: str = NotProvided,
        assets_to_preload: list[str] = NotProvided,
        animation_configs: list = NotProvided,
    ):
        if env_to_state_fn is not NotProvided:
            self.env_to_state_fn = env_to_state_fn

        if hud_text_fn is not NotProvided:
            self.hud_text_fn = hud_text_fn

        if preload_specs is not NotProvided:
            self.preload_specs = preload_specs

        if location_representation is not NotProvided:
            assert location_representation in [
                "relative",
                "pixels",
            ], "Must pass either relative or pixel location!"
            self.location_representation = location_representation

        if fps is not NotProvided:
            self.fps = fps

        if game_width is not NotProvided:
            self.game_width = game_width

        if game_height is not NotProvided:
            self.game_height = game_height

        if background is not NotProvided:
            self.background = background

        if state_init is not NotProvided:
            self.state_init = state_init

        if assets_dir is not NotProvided:
            self.assets_dir = assets_dir

        if assets_to_preload is not NotProvided:
            self.assets_to_preload = assets_to_preload

        if animation_configs is not NotProvided:
            self.animation_configs = animation_configs

        return self

    def policies(
        self,
        policy_mapping: dict = NotProvided,
        load_policy_fn: Callable = NotProvided,
        policy_inference_fn: Callable = NotProvided,
        frame_skip: int = NotProvided,
    ):
        if policy_mapping is not NotProvided:
            self.policy_mapping = policy_mapping

        if load_policy_fn is not NotProvided:
            self.load_policy_fn = load_policy_fn

        if policy_inference_fn is not NotProvided:
            self.policy_inference_fn = policy_inference_fn

        if frame_skip is not NotProvided:
            self.frame_skip = frame_skip

        return self

    def gameplay(
        self,
        action_mapping: dict = NotProvided,
        human_id: str | int = NotProvided,
        num_episodes: int = NotProvided,
        default_action: int | str = NotProvided,
        action_population_method: str = NotProvided,
        input_mode: str = NotProvided,
        callback: None = NotProvided,  # TODO(chase): add callback typehint without circular import
        reset_freeze_s: int = NotProvided,
    ):
        if action_mapping is not NotProvided:
            # ensure the composite action tuples are sorted
            sorted_tuple_action_map = {}
            for k, v in action_mapping.items():
                if isinstance(k, tuple):
                    self.game_has_composite_actions = True
                    sorted_tuple_action_map[tuple(sorted(k))] = v
                else:
                    sorted_tuple_action_map[k] = v
            self.action_mapping = action_mapping

        if action_population_method is not NotProvided:
            self.action_population_method = action_population_method

        if human_id is not NotProvided:
            self.human_id = human_id

        if num_episodes is not NotProvided:
            assert (
                type(num_episodes) == int and num_episodes >= 1
            ), "Must pass an int >=1 to num episodes."
            self.num_episodes = num_episodes

        if default_action is not NotProvided:
            self.default_action = default_action

        if input_mode is not NotProvided:
            self.input_mode = input_mode

        if callback is not NotProvided:
            self.callback = callback

        if reset_freeze_s is not NotProvided:
            self.reset_freeze_s = reset_freeze_s

        return self

    def user_experience(
        self,
        scene_header: str = NotProvided,
        scene_body: str = NotProvided,
        scene_body_filepath: str = NotProvided,
        in_game_scene_body: str = NotProvided,
        in_game_scene_body_filepath: str = NotProvided,
        waitroom_timeout_redirect_url: str = NotProvided,
        game_page_html_fn: Callable = NotProvided,
    ):
        if scene_header is not NotProvided:
            self.scene_header = scene_header

        if waitroom_timeout_redirect_url is not NotProvided:
            self.waitroom_timeout_redirect_url = waitroom_timeout_redirect_url

        # if append_subject_id_to_redirect is not NotProvided:
        #     self.append_subject_id_to_redirect = append_subject_id_to_redirect

        if game_page_html_fn is not NotProvided:
            self.game_page_html_fn = game_page_html_fn

        if scene_body_filepath is not NotProvided:
            assert (
                self.scene_body is None and scene_body is NotProvided
            ), "Cannot set both filepath and html_body."

            with open(scene_body_filepath, "r", encoding="utf-8") as f:
                self.scene_body = f.read()

        if scene_body is not NotProvided:
            assert (
                scene_body_filepath is NotProvided
            ), "Cannot set both filepath and html_body."
            self.scene_body = scene_body

        if in_game_scene_body_filepath is not NotProvided:
            assert (
                self.in_game_scene_body is NotProvided
                and in_game_scene_body is NotProvided
            ), "Cannot set both filepath and html_body."

            with open(in_game_scene_body_filepath, "r", encoding="utf-8") as f:
                self.in_game_scene_body = f.read()

        if in_game_scene_body is not NotProvided:
            assert (
                in_game_scene_body_filepath is NotProvided
            ), "Cannot set both filepath and html_body."
            self.in_game_scene_body = in_game_scene_body

        return self

    def pyodide(
        self,
        run_through_pyodide: bool = NotProvided,
        environment_initialization_code: str = NotProvided,
        environment_initialization_code_filepath: str = NotProvided,
        packages_to_install: list[str] = NotProvided,
    ):
        if run_through_pyodide is not NotProvided:
            assert isinstance(run_through_pyodide, bool)
            self.run_through_pyodide = run_through_pyodide

        if environment_initialization_code is not NotProvided:
            self.environment_initialization_code = (
                environment_initialization_code
            )

        if environment_initialization_code_filepath is not NotProvided:
            assert (
                environment_initialization_code is NotProvided
            ), "Cannot set both filepath and code!"
            with open(
                environment_initialization_code_filepath, "r", encoding="utf-8"
            ) as f:
                self.environment_initialization_code = f.read()

        if packages_to_install is not NotProvided:
            self.packages_to_install = packages_to_install

        return self

    @property
    def simulate_waiting_room(self) -> bool:
        """
        Returns a boolean indicating whether or not we're
        forcing all participants to be in a waiting room, regardless
        of if they're waiting for other players or not.
        """
        return max(self.waitroom_time_randomization_interval_s) > 0

    def get_complete_scene_metadata(self) -> dict:
        """ """
        metadata = super().scene_metadata

        # Add all of the class properties to the metadata
        for k, v in self.__dict__.items():
            if k not in metadata and k != "sio":
                if (
                    isinstance(v, (str, int, float, bool, list, dict))
                    or v is None
                ):
                    metadata[k] = v
                elif hasattr(v, "__dict__"):
                    metadata[k] = v.__dict__
                else:
                    metadata[k] = str(v)

        return metadata
