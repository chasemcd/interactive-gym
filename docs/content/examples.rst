Examples
=========

We provide two examples of using Interactive Gym, first is an example of using Slime Volleyball and the second is an example of using CoGrid Overcooked. The former 
relies on using the primitive shape rendering provided in Interactive Gym, whereas the latter uses a sprite sheet for graphics.


Slime Volleyball
-----------------

Slime Volleyball is a simple game where two players control a slime and try to hit a ball over a net. A simulation environment for it
was originally developed by David Ha (https://github.com/hardmaru/slimevolleygym). This original library is no longer maintained, but a Jax 
version is through EvoJax (https://github.com/google/evojax/blob/main/evojax/task/slimevolley.py). In our example, we use a fork of the original
implementation that has been updated to the Gymnasium API. The fork is available at https://github.com/chasemcd/slimevolleygym.


First, create an instance of the ``RemoteConfig`` class. This class is used to configure the Interactive Gym environment.

.. code-block:: python
    
    config = RemoteConfig()


Now, we walk step-by-step through each component of the the Interactive Gym ``RemoteConfig`` for Slime Volleyball.
First, for the environment instantiation, we must define the ``env_creator`` function, which is called to 
return an instance of the environment. 

.. code-block:: python

    def env_creator(*args, **kwargs):
        config = {"human_inputs": True}
        return slimevolley_env.SlimeVolleyEnv(config=config)
 
    config = config.environment(
        env_creator=env_creator
    )

Next, we define the ``gameplay`` settings. This defines how actions are taken, the number of interactions, and how 
data collection will occur. First, we define all of the actions (which in some cases may be an attribute of the environment).
Then, we map each of the actions to the Javascript keycodes that will be used to trigger them. A default action is also provided,
which specifies the action to take when no keypress is received. We also set the `action_population_method`,
which dictates how we will fill in missing actions when none are received on the server (e.g., we haven't received a default action or input).
Finally, we define the number of episodes to run and the callback to use. The callback is used to collect data from the environment.

.. code-block:: python

    NOOP = 0
    LEFT = 1
    UPLEFT = 2
    UP = 3
    UPRIGHT = 4
    RIGHT = 5

    action_mapping = {
        "ArrowLeft": LEFT,
        ("ArrowLeft", "ArrowUp"): UPLEFT,
        "ArrowUp": UP,
        ("ArrowRight", "ArrowUp"): UPRIGHT,
        "ArrowRight": RIGHT,
    }

    class SlimeVolleyballCallback(callback.GameCallback):
        def __init__(self) -> None:
            self.start_times = {}
            self.states = collections.defaultdict(list)
            self.actions = collections.defaultdict(list)
            self.rewards = collections.defaultdict(list)

        def on_episode_start(self, remote_game: RemoteGame) -> None:
            self.start_times[remote_game.game_uuid] = time.time()

        def on_episode_end(self, remote_game: RemoteGame) -> None:
            self.save_and_clear_data(remote_game)

        def on_game_tick_start(self, remote_game: RemoteGame) -> None:
            """
            At the beginning of the tick() call, we'll log the current state of the game.
            """
            self.states[remote_game.game_uuid].append(
                self.gen_game_data(remote_game)
            )

        def on_game_tick_end(self, remote_game: RemoteGame) -> None:
            """
            At the end of the tick() call, log the actions taken and the reward earned.
            """
            actions = {
                f"{a_id}_action": action
                for a_id, action in remote_game.prev_actions.items()
            }
            rewards = {
                f"{a_id}_reward": reward
                for a_id, reward in remote_game.prev_rewards.items()
            }

            self.actions[remote_game.game_uuid].append(actions)
            self.rewards[remote_game.game_uuid].append(rewards)

        # [... see full code in examples/slime_volleyball/slime_volleyball_callback.py...]


    config = config.gameplay(
        default_action=NOOP,
        action_population_method=ActionSettings.PreviousSubmittedAction,
        action_mapping=action_mapping,
        num_episodes=10,
        callback=SlimeVolleyballCallback(),
    )





CoGrid Overcooked
------------------

[... coming soon, see examples/cogrid_overcooked/ ...]

