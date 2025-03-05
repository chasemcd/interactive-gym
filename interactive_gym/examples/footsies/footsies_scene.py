from interactive_gym.scenes import unity_scene
import flask_socketio
import dataclasses
import random

from interactive_gym.scenes.scene import Scene


@dataclasses.dataclass
class OpponentConfig:
    model_path: str
    frame_skip: int = 4
    obs_delay: int = 16
    inference_cadence: int = 4
    softmax_temperature: float = 1.0


class FootsiesScene(unity_scene.UnityScene):
    def __init__(self):
        super().__init__()
        self.winners: list[str] = []
        self.opponent_sequence: list[OpponentConfig] = [
            OpponentConfig(
                model_path="4sf-16od-1c73fcc-0.03to0.01-500m-00",
                frame_skip=4,
                obs_delay=16,
                inference_cadence=4,
                softmax_temperature=1.0,
            )
        ]
        self.randomize_opponents: bool = False

    def build(self) -> list[Scene]:
        if self.randomize_opponents:
            random.shuffle(self.opponent_sequence)
        return super().build()

    def set_opponent_sequence(
        self, opponents: list[OpponentConfig], randomize: bool = False
    ):
        self.opponent_sequence = opponents
        self.randomize_opponents = randomize
        return self

    def on_unity_episode_start(
        self, data: dict, sio: flask_socketio.SocketIO, room: str
    ):

        if len(self.opponent_sequence) == 0:
            super().on_unity_episode_start(data, sio, room)
            return

        opponent_config = self.opponent_sequence.pop(0)

        sio.emit(
            "updateBotSettings",
            {
                "modelPath": opponent_config.model_path,
                "frameSkip": opponent_config.frame_skip,
                "inferenceCadence": opponent_config.inference_cadence,
                "observationDelay": opponent_config.obs_delay,
                "softmaxTemperature": opponent_config.softmax_temperature,
            },
        )


class FootsiesDynamicDifficultyScene(FootsiesScene):
    def __init__(self):
        super().__init__()
        self.winners: list[str] = []
        self.model_path: str = "4sf-16od-1c73fcc-0.03to0.01-500m-00"
        self.cur_frame_skip: int = 12
        self.cur_obs_delay: int = 16
        self.cur_inference_cadence: int = 4
        self.cur_softmax_temperature: float = 1.4

        self.min_frame_skip: int = 4
        self.max_frame_skip: int = 24
        self.frame_skip_step: int = 2
        self.min_temperature: float = 1.0
        self.max_temperature: float = 1.7
        self.temperature_step: float = 0.1

        self.opponent_sequence: list[OpponentConfig] = [
            OpponentConfig(
                model_path=self.model_path,
                frame_skip=self.cur_frame_skip,
                obs_delay=self.cur_obs_delay,
                inference_cadence=self.cur_inference_cadence,
                softmax_temperature=self.cur_softmax_temperature,
            )
        ]

    def set_initial_settings(
        self,
        model_path: str,
        frame_skip: int = 4,
        obs_delay: int = 16,
        inference_cadence: int = 4,
        softmax_temperature: float = 1.0,
    ):
        self.model_path = model_path
        self.cur_frame_skip = frame_skip
        self.cur_obs_delay = obs_delay
        self.cur_inference_cadence = inference_cadence
        self.cur_softmax_temperature = softmax_temperature

    def on_unity_episode_end(
        self, data: dict, sio: flask_socketio.SocketIO, room: str
    ):
        winner = data["winner"]
        self.winners.append(winner)

        if len(self.winners) >= 2:

            # If P1 (human) won twice in a row, make the opponent harder.
            if all(w == "P1" for w in self.winners[-2:]):
                self.cur_frame_skip = max(
                    self.min_frame_skip,
                    self.cur_frame_skip - self.frame_skip_step,
                )
                self.cur_softmax_temperature = min(
                    self.max_temperature,
                    self.cur_softmax_temperature - self.temperature_step,
                )

            # If P2 (bot) won twice in a row, make the opponent easier.
            elif all(w == "P2" for w in self.winners[-2:]):
                self.cur_frame_skip = min(
                    self.max_frame_skip,
                    self.cur_frame_skip + self.frame_skip_step,
                )
                self.cur_softmax_temperature = max(
                    self.min_temperature,
                    self.cur_softmax_temperature + self.temperature_step,
                )

        self.opponent_sequence.append(
            OpponentConfig(
                model_path=self.model_path,
                frame_skip=self.cur_frame_skip,
                obs_delay=self.cur_obs_delay,
                inference_cadence=self.cur_inference_cadence,
                softmax_temperature=self.cur_softmax_temperature,
            )
        )
        super().on_unity_episode_end(data, sio, room)


class FootsiesDynamicEmpowermentScene(FootsiesScene):
    def __init__(self):
        super().__init__()
        self.winners: list[str] = []
        self.model_path: str = "4sf-16od-1c73fcc-0.03to0.01-500m-00"
        self.cur_frame_skip: int = 4
        self.cur_obs_delay: int = 16
        self.cur_inference_cadence: int = 4
        self.cur_softmax_temperature: float = 1.0
        self.cur_model_idx = 0

        self.model_paths: list[str] = [
            "esr-1.0alpha-00",
            "esr-0.5alpha-00",
            "esr-0.25alpha-00",
            "4sf-16od-1c73fcc-0.03to0.01-500m-00",
            "4sf-16od-1c73fcc-0.03to0.01-500m-00",
        ]

        self.opponent_sequence: list[OpponentConfig] = [
            OpponentConfig(
                model_path=self.model_paths[self.cur_model_idx],
                frame_skip=(
                    8
                    if self.cur_model_idx == len(self.model_paths) - 2
                    else self.cur_frame_skip
                ),
                obs_delay=self.cur_obs_delay,
                inference_cadence=self.cur_inference_cadence,
                softmax_temperature=self.cur_softmax_temperature,
            )
        ]

    def set_initial_settings(
        self,
        model_path: str,
        frame_skip: int = 4,
        obs_delay: int = 16,
        inference_cadence: int = 4,
        softmax_temperature: float = 1.0,
    ):
        self.model_path = model_path
        self.cur_frame_skip = frame_skip
        self.cur_obs_delay = obs_delay
        self.cur_inference_cadence = inference_cadence
        self.cur_softmax_temperature = softmax_temperature

    def on_unity_episode_end(
        self, data: dict, sio: flask_socketio.SocketIO, room: str
    ):
        winner = data["winner"]
        self.winners.append(winner)

        if len(self.winners) >= 2:

            # If P1 (human) won twice in a row, make the opponent harder.
            if all(w == "P1" for w in self.winners[-2:]):
                self.cur_model_idx = min(
                    len(self.model_paths) - 1,
                    self.cur_model_idx + 1,
                )

            # If P2 (bot) won twice in a row, make the opponent easier.
            elif all(w == "P2" for w in self.winners[-2:]):
                self.cur_model_idx = max(0, self.cur_model_idx - 1)

        self.opponent_sequence.append(
            OpponentConfig(
                model_path=self.model_paths[self.cur_model_idx],
                frame_skip=(
                    8
                    if self.cur_model_idx == len(self.model_paths) - 2
                    else self.cur_frame_skip
                ),
                obs_delay=self.cur_obs_delay,
                inference_cadence=self.cur_inference_cadence,
                softmax_temperature=self.cur_softmax_temperature,
            )
        )
        super().on_unity_episode_end(data, sio, room)


class FootsiesRandomDifficultyScene(FootsiesScene):
    def __init__(self):
        super().__init__()
        self.winners: list[str] = []
        self.model_path: str = "4sf-16od-1c73fcc-0.03to0.01-500m-00"
        self.fs_temp_options: list[tuple[int, float]] = [
            (32, 1.7),  # Easiest
            (24, 1.6),
            (14, 1.5),
            (12, 1.4),
            (10, 1.3),
            (8, 1.2),
            (6, 1.1),
            (4, 1.0),  # Hardest
        ]
        self.cur_obs_delay: int = 16
        self.cur_inference_cadence: int = 4

    def on_unity_episode_start(
        self, data: dict, sio: flask_socketio.SocketIO, room: str
    ):
        sampled_options = random.choice(self.fs_temp_options)
        frame_skip, softmax_temperature = sampled_options

        self.opponent_sequence.append(
            OpponentConfig(
                model_path=self.model_path,
                frame_skip=frame_skip,
                obs_delay=self.cur_obs_delay,
                inference_cadence=self.cur_inference_cadence,
                softmax_temperature=softmax_temperature,
            )
        )
        super().on_unity_episode_end(data, sio, room)


class FootsiesControllableDifficultyScene(FootsiesScene):
    def __init__(self):
        super().__init__()

        self.configuration_mapping: dict[int, OpponentConfig] = {
            0: OpponentConfig(
                model_path="4sf-16od-1c73fcc-0.03to0.01-500m-00",
                frame_skip=32,
                obs_delay=16,
                inference_cadence=4,
                softmax_temperature=1.7,
            ),
            1: OpponentConfig(
                model_path="4sf-16od-1c73fcc-0.03to0.01-500m-00",
                frame_skip=24,
                obs_delay=16,
                inference_cadence=4,
                softmax_temperature=1.6,
            ),
            2: OpponentConfig(
                model_path="44sf-16od-1c73fcc-0.03to0.01-500m-00",
                frame_skip=14,
                obs_delay=16,
                inference_cadence=4,
                softmax_temperature=1.5,
            ),
            3: OpponentConfig(
                model_path="4sf-16od-1c73fcc-0.03to0.01-500m-00",
                frame_skip=12,
                obs_delay=16,
                inference_cadence=4,
                softmax_temperature=1.4,
            ),
            4: OpponentConfig(
                model_path="4sf-16od-1c73fcc-0.03to0.01-500m-00",
                frame_skip=10,
                obs_delay=16,
                inference_cadence=4,
                softmax_temperature=1.3,
            ),
            5: OpponentConfig(
                model_path="4sf-16od-1c73fcc-0.03to0.01-500m-00",
                frame_skip=8,
                obs_delay=16,
                inference_cadence=4,
                softmax_temperature=1.2,
            ),
            6: OpponentConfig(
                model_path="4sf-16od-1c73fcc-0.03to0.01-500m-00",
                frame_skip=6,
                obs_delay=16,
                inference_cadence=4,
                softmax_temperature=1.1,
            ),
            7: OpponentConfig(
                model_path="4sf-16od-1c73fcc-0.03to0.01-500m-00",
                frame_skip=4,
                obs_delay=16,
                inference_cadence=4,
                softmax_temperature=1.0,
            ),
        }
        self.opponent_sequence: list[OpponentConfig] = []

    def on_client_callback(
        self, data: dict, sio: flask_socketio.SocketIO, room: str
    ):
        print(f"Received client callback: {data}")
        if data.get("type") == "updateFootsiesDifficulty":
            opponent_config = self.configuration_mapping.get(data["difficulty"])
            self.opponent_sequence = [opponent_config]

            sio.emit(
                "updateBotSettings",
                {
                    "modelPath": opponent_config.model_path,
                    "frameSkip": opponent_config.frame_skip,
                    "inferenceCadence": opponent_config.inference_cadence,
                    "observationDelay": opponent_config.obs_delay,
                    "softmaxTemperature": opponent_config.softmax_temperature,
                },
            )
