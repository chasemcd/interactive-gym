from interactive_gym.scenes import unity_scene
import flask_socketio
import dataclasses
import random


@dataclasses.dataclass
class OpponentConfig:
    model_path: str
    frame_skip: int = 4
    obs_delay: int = 16
    inference_cadence: int = 4
    softmax_temperature: float = 1.0


# TODO(chase): need to add a way to update the opponent before
# the first round starts. We need an "initial opponent" that
# is set before the first round starts.

# Unity should emit an "onGameInitialized" event when the game is initialized,
# and we respond to it with the initial opponent.


class FootsiesScene(unity_scene.UnityScene):
    def __init__(self):
        super().__init__()
        self.winners: list[str] = []
        self.opponent_sequence: list[OpponentConfig] = []

    def set_opponent_sequence(self, opponents: list[OpponentConfig]):
        self.opponent_sequence = opponents

    def on_unity_game_initialized(
        self, data: dict, sio: flask_socketio.SocketIO, room: str
    ):
        if len(self.opponent_sequence) == 0:
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

    def on_unity_episode_end(
        self, data: dict, sio: flask_socketio.SocketIO, room: str
    ):
        if len(self.opponent_sequence) == 0:
            super().on_unity_episode_end(data, sio, room)
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

        super().on_unity_episode_end(data, sio, room)


class FootsiesDynamicDifficultyScene(FootsiesScene):
    def __init__(self):
        super().__init__()
        self.winners: list[str] = []
        self.model_path: str = "4fs-16od-13c7f7b-0.05to0.01-sp-03"
        self.cur_frame_skip: int = 12
        self.cur_obs_delay: int = 16
        self.cur_inference_cadence: int = 4
        self.cur_softmax_temperature: float = 1.4

        self.min_frame_skip: int = 4
        self.max_frame_skip: int = 32
        self.frame_skip_step: int = 2
        self.min_temperature: float = 1.0
        self.max_temperature: float = 1.7
        self.temperature_step: float = 0.1

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

        if len(self.winners) > 2:

            # If P1 (human) won twice in a row, make the opponent harder.
            if all(w == "P1" for w in self.winners[-2:]):
                print("P1 won twice in a row, making the opponent harder.")
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
                print("P2 won twice in a row, making the opponent easier.")
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


class FootsiesControllableDifficultyScene(FootsiesScene):
    def __init__(self):
        super().__init__()

        self.configuration_mapping: dict[int, OpponentConfig] = {}
