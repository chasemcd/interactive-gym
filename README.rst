Interactive Gym
================

.. image:: interactive_gym_logo.png
    :alt: Interactive Gym Logo
    :align: center

.. raw:: html

   <div style="background-color: #f0f0f0; border: 2px solid #ff0000; padding: 10px; margin: 10px 0;">
   <h3 style="color: #ff0000;">⚠️ Warning</h3>

.. warning::
    Interactive Gym is currently under heavy development and not all functionality is available, as we are currently refactoring to allow for increased flexibility
    and functionality. The documentation is also currently being rewritten to reflect the current state of the library.
    To view the version associated with the McDonald & Gonzalez (2024) paper, please see the `v0.0.1 release <https://github.com/chasemcd/interactive-gym/releases/tag/v0.0.1>`_.

.. raw:: html

   </div>

----


Interactive Gym is a library that provides a simple interface for creating interactive, browser-based experiments from simulation environments.

There are two ways to run Interactive Gym, depending on your use cases and requirements:

1. Server based. 

This runs the environment on a server, allows for any number of human and AI players. 
At every step, the server will send the required information to all connected clients 
to update the environment client-side (e.g., the locations and any relevant data of updated objects).

2. Browser based. 

This runs the environment in the browser using `Pyodide <https://pyodide.org/>`_. This approach has several limitations: the environment must be pure python and 
only a single human player is supported (although you may add any number of AI players). The benefit of this approach is that you circumvent (almsot) all of the issues
associated with client server communication. Indeed, if participants do not have a stable internet connection (or are far from your sever), fast client-server communication
can't be guaranteed and participant experience may degrade. In the browser-based approach, we also conduct model inference in the browser via ONNX.

Usage
------

At a high level, an Interactive Gym experiment is defined by a set of scenes. 
Each scene defines what should be displayed to participants and what interactions can 
occur. 

There are two core types of scenes: ``StaticScene`` and ``GymScene``. The former just
displays static informaiton to clients and can also be used to collect some forms of data 
(e.g., text boxes, option buttons, etc.). The latter defines an interaction with a simulation 
environment and is where the core interactions occur. 

Interactive Gym utilizes a ``Stager``, which manages participants' progression through a sequence
of scenes. A ``Stager`` is initialized with a list of scenes and, when a participant joins, a stager
is initialized for that participant to track their progress through the scenes. 

A sequence of scenes must start with a ``StartScene`` and end with an ``EndScene``, both of which
are particular instances of a ``StaticScene``. At each ``StartScene`` and all intermediate ``StaticScene`` instances, 
a "Continue" button is displayed to allow participants to advance to the next scene. It is also possible to disable this button
until some condition is met (e.g., a participant must complete a particular action or selection before 
advancing).

A ``GymScenes`` takes in all parameters to configure interaction with a 
simulation environment (in ``PettingZoo`` parallel environment format).

The structure of an Interactive Gym experiment is as follows:

.. code-block:: python

    start_scene = (
        static_scene.StartScene()
        .scene(
            scene_id="my_start_scene",
        )
        .display(
            scene_header="Welcome to my Interactive Gym Experiment!",
            scene_body_filepath="This is an example body text for a start scene.",
        )
    )

    my_gym_scene = (
        gym_scene.GymScene()
        # Define all GymScene parameters here with the 
        # various GymScene configuration functions.
        # [...]
    )

    end_scene = static_scene.EndScene().display(
        scene_header="Thank you for playing!",
    )

    stager = stager.Stager(scenes=[start_scene, my_gym_scene, end_scene])


    if __name__ == "__main__":
        experiment_config = (
            experiment_config.ExperimentConfig()
            .experiment(stager=stager, experiment_id="my_experiment")
            .hosting(port=8000, host="0.0.0.0")
        )

        app.run(experiment_config)

Structure
-------------

The repository has the following structure:

.. code-block:: bash

    ├── README.rst
    ├── docs
    ├── down.sh
    ├── interactive_gym
    │   ├── configurations
    │   │   ├── configuration_constants.py
    │   │   ├── experiment_config.py
    │   │   ├── interactive-gym-nginx.conf
    │   │   ├── object_contexts.py
    │   │   ├── remote_config.py
    │   │   └── render_configs.py
    │   ├── examples
    │   ├── scenes
    │   │   ├── constructors
    │   │   │   ├── constructor.py
    │   │   │   ├── options.py
    │   │   │   └── text.py
    │   │   ├── gym_scene.py
    │   │   ├── scene.py
    │   │   ├── stager.py
    │   │   ├── static_scene.py
    │   │   └── utils.py
    │   ├── server
    │   │   ├── app.py
    │   │   ├── callback.py
    │   │   ├── game_manager.py
    │   │   ├── remote_game.py
    │   │   ├── server_app.py
    │   │   ├── static
    │   │   │   ├── assets
    │   │   │   ├── js
    │   │   │   │   ├── game_events.js
    │   │   │   │   ├── index.js
    │   │   │   │   ├── index_beta.js
    │   │   │   │   ├── latency.js
    │   │   │   │   ├── msgpack.min.js
    │   │   │   │   ├── onnx_inference.js
    │   │   │   │   ├── phaser_gym_graphics.js
    │   │   │   │   ├── pyodide_remote_game.js
    │   │   │   │   ├── socket_handlers.js
    │   │   │   │   └── ui_utils.js
    │   │   │   ├── lib
    │   │   │   └── templates
    │   │   │       ├── index.html
    │   │   └── utils.py
    │   └── utils
    │       ├── inference_utils.py
    │       ├── onnx_inference_utils.py
    │       └── typing.py
    ├── requirements.txt
    └── up.sh


Acknowledgements
---------------------

The Phaser integration and server implementation are inspired by and derived from the 
Overcooked AI demo by Carroll et al. (https://github.com/HumanCompatibleAI/overcooked-demo/tree/master).


