Interactive Gym
================

.. image:: docs/interactive_gym_logo.png
    :alt: Interactive Gym Logo
    :align: center

Interactive Gym is a library that provides a simple interface for creating interactive, browser-based experiments from simulation environments.

Structure
-------------

The repository has the following structure:

.. code-block:: bash

    ├── README.md
    ├── __pycache__
    ├── configurations
    │   ├── configuration_constants.py
    │   ├── object_contexts.py
    │   ├── remote_config.py
    │   └── render_configs.py
    ├── examples
    ├── requirements.txt
    ├── server
    │   ├── callback.py
    │   ├── remote_game.py
    │   ├── server_app.py
    │   ├── static
    │   │   ├── assets
    │   │   ├── js
    │   │   ├── lib
    │   │   └── templates
    │   └── utils.py
    └── utils
        ├── inference_utils.py
        └── onnx_inference_utils.py



The ``server/`` directory provides all functionality to execute rendering and client-facing interfaces. ``server_app.py`` defines the Flask app that serves information to the front end, for which all templates are included in ``server/static/``.
The ``remote_game.py`` file defines the logic that operates over a ``gymnasium`` environment.

Callbacks can be used for data logging and provide hooks for a user to execute specific code at various points in the user experiences, their definition is in ``server/callback.py``


Usage
------

To run an interactive experiment, a user should define a file with the following general structure:

.. code-block:: python

    from configurations import remote_config
    from server import server_app
    from configurations import configuration_constants

    # Define the allowed actions in the game
    MoveUp = 0
    MoveDown = 1
    MoveLeft = 2
    MoveRight = 3
    Noop = 4


    # Map the players to humans or AI
    POLICY_MAPPING = {
        "player-0": configuration_constants.PolicyTypes.Human,
        "player-1": YOUR_AI_POLICY,
    }


    # Define a function that instantiates a gymnasium environment
    def env_creator(*args, **kwargs):
        """Generic function to return the Gymnasium environment"""
        return YOUR_ENVIRONMENT_CLASS(*args, **kwargs)


    # Map the actions to the arrow keys. The keys are Javascript key press events (all others ignored)
    action_mapping = {
        "ArrowLeft": MoveLeft,
        "ArrowRight": MoveRight,
        "ArrowUp": MoveUp,
        "ArrowDown": MoveDown,
    }



    # The RemoteConfig class describes all
    # options that you can set in configuring your experiment.
    # There are significantly more options defined in the RemoteConfig class.
    config = (
        remote_config.RemoteConfig()
        .policies(
            policy_mapping=POLICY_MAPPING,
            policy_inference_fn=...,  # function to get an action from your AI
            load_policy_fn=...,  # function to load your AI from the string name
            frame_skip=4,  # how often does the AI act in terms of frames?
        )
        .environment(env_creator=env_creator)
        .rendering(
            fps=24,  # FPS of the environment
            env_to_state_fn=..., # pass a function that goes from env -> canvas objects
            game_width=...,  # pixel width
            game_height=..., # pixel height
        )
        .gameplay(
            default_action=Noop,  # when a player doesn't press an action, what should they do?
            action_mapping=action_mapping,
            num_episodes=..., # number of episodes each participant sees
            input_mode=...,  # see configuration_constants.py for options
            callback=YourCallback(),  # defines data collection
        )
        .hosting(port=5703, host="0.0.0.0")
    )


    if __name__ == "__main__":
        server_app.run(config)


Examples
---------

Two examples are provided: CoGrid Overcooked and Slime Volleyball. Interactive experiments with humans and AI or human-human pairs can be run, respectively, via the following commands.

CoGrid Overcooked

.. code-block:: bash

    python -m examples.cogrid_overcooked.overcooked_human_ai_server
    python -m examples.cogrid_overcooked.overcooked_human_human_server

Slime Volleyball

.. code-block:: bash

    python -m examples.slime_volleyball.slime_volleyball_human_ai_server
    python -m examples.slime_volleyball.slime_volleyball_human_human_server

Instructions for installation can be found in the respective README.md files in the ``examples/`` directory.

In both examples we follow the same file structure with three key files:
1. ``{game}_callback.py``: This file defines how we collect data using hooks in the app.
2. ``{game}_*_server.py``: This file launches the app for a particular experiment.
3. ``{game}_utils.py``: In the utils file, we define the process by which we render objects in the browser (e.g., defining a function that specifies sprite relationship, canvas objects, etc.).

Example AI policies as ONNX files are also included in the ``policies/`` directory.

Acknowledgements
---------------------

The Phaser integration and server implementation are inspired by and derived from the Overcooked AI demo by Carroll et al. (https://github.com/HumanCompatibleAI/overcooked-demo/tree/master).




Installation
------------
To install Interactive Gym, you can use the PyPi distribution:

    .. code-block:: bash

        pip install interactive-gym

Or directly from the master branch:

    .. code-block:: bash

        pip install git+https://www.github.com/DDM-Lab/interactive-gym.git
