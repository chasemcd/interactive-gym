import typing


class RemoteConfig:
    def __init__(self):
        self.env_creator: typing.Callable | None = None
        self.env_name: str | None = None
        self.seed: int = 42

        # hosting
        self.host = None
        self.port = 8000

        # policies
        self.policy_mapping: dict[str, typing.Any] = {}
        self.available_policies: dict[str, typing.Any] = {}
        self.policy_configs: dict[str, typing.Any] = {}
        self.frame_skip: int = 4

        # gameplay
        self.num_episodes: int = 1
        self.action_mapping: dict[str, int] = {}
        self.human_id: str | int | None = None
        self.default_action: int | str | None = None

        # rendering
        self.env_to_state_fn: typing.Callable | None = None
        self.game_width: int | None = None
        self.game_height: int | None = None

        # user_experience
        self.redirect_url: str | None = None  # send user here after experiment.
        self.screen_size: int | None = None
        self.game_header_text: str = "Game Page Header"
        self.start_header_text: str = "Start Page Header"
        self.start_page_text: str = "Start Page Text"
        self.game_page_text: str = "Game Page Text"
        self.fps: int = 10

    def environment(
        self,
        env_creator: typing.Callable | None = None,
        env_name: str | None = None,
        seed: int | None = None,
    ):
        if env_creator is not None:
            self.env_creator = env_creator

        if env_name is not None:
            self.env_name = env_name

        if seed is not None:
            self.seed = seed

        return self

    def rendering(self, env_to_state_fn: typing.Callable | None = None):
        if env_to_state_fn is not None:
            self.env_to_state_fn = env_to_state_fn

        return self

    def hosting(self, host: str | None = None, port: int | None = None):
        if host is not None:
            self.host = host

        if port is not None:
            self.port = port

        return self

    def policies(
        self,
        policy_mapping: dict | None = None,
        available_policies: dict | None = None,
        policy_configs: dict | None = None,
        frame_skip: int | None = None,
    ):
        if policy_mapping is not None:
            self.policy_mapping = policy_mapping

        if available_policies is not None:
            self.available_policies = available_policies

        if policy_configs is not None:
            self.policy_configs = policy_configs

        if frame_skip is not None:
            self.frame_skip = frame_skip

        return self

    def gameplay(
        self,
        action_mapping: dict | None = None,
        human_id: str | int | None = None,
        num_episodes: int | None = None,
        default_action: int | str | None = None,
    ):
        if action_mapping is not None:
            self.action_mapping = action_mapping

        if human_id is not None:
            self.human_id = human_id

        if num_episodes is not None:
            assert (
                type(num_episodes) == 1 and num_episodes >= 1
            ), "Must pass an int >=1 to num episodes."
            self.num_episodes = num_episodes

        if default_action is not None:
            self.default_action = default_action

        return self

    def user_experience(
        self,
        redirect_url: str | None = None,
        screen_size: int | None = None,
        start_header_text: str | None = None,
        game_header_text: str | None = None,
        game_page_text: str | None = None,
        start_page_text: str | None = None,
        fps: int | None = None,
    ):
        if redirect_url is not None:
            self.redirect_url = redirect_url

        if screen_size is not None:
            self.screen_size = screen_size

        if start_header_text is not None:
            self.start_header_text = start_header_text

        if game_header_text is not None:
            self.game_header_text = game_header_text

        if start_page_text is not None:
            self.start_page_text = start_page_text

        if game_page_text is not None:
            self.game_page_text = game_page_text

        if fps is not None:
            self.fps = fps

        return self
