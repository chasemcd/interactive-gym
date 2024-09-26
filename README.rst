Interactive Gym
================

.. image:: docs/interactive_gym_logo.png
    :alt: Interactive Gym Logo
    :align: center

Interactive Gym is a library that provides a simple interface for creating interactive, browser-based experiments from simulation environments.

There are two ways to run Interactive Gym, depending on your use cases and requirements:

1. Server based. This runs the environment on a server, allows for any number of human and AI players. At every step, the server will send the required information 
    to all connected clients to update the environment client-side (e.g., the locations and any relevant data of updated objects).
2. Browser based. This runs the environment in the browser using `Pyodide <https://pyodide.org/>`_. This approach has several limitations: the environment must be pure python and 
    only a single human player is supported (although you may add any number of AI players). The benefit of this approach is that you circumvent all of the issues
    associated with client server communication. Indeed, if participants do not have a stable internet connection (or are far from your sever), fast client-server communication
    can't be guaranteed and participant experience may degrade. In the browser-based approach, we also conduct model inference in the browser via ONNX.

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


The ``server/`` directory provides all functionality to execute rendering and client-facing interfaces. ``app.py`` defines the Flask app that serves information to the front end, for which all templates are included in ``server/static/``.
The ``remote_game.py`` file defines the logic that operates over a ``gymnasium`` environment.

Callbacks can be used for data logging and provide hooks for a user to execute specific code at various points in the user experiences, their definition is in ``server/callback.py``


Usage
------

To run an interactive experiment, a user should define a file with the following general structure:

.. code-block:: python

    # TODO


Examples
---------

Two examples are provided: CoGrid Overcooked and Slime Volleyball. Interactive experiments with humans and AI or human-human pairs can be run, respectively, via the following commands.

CoGrid Overcooked

.. code-block:: bash

    python -m examples.cogrid_overcooked.human_ai_server
    python -m examples.cogrid_overcooked.human_human_server
    python -m examples.cogrid_overcooked.human_ai_pyodide

Slime Volleyball

.. code-block:: bash

    python -m examples.slime_volleyball.human_ai_server
    python -m examples.slime_volleyball.human_human_server

Instructions for installation can be found in the respective README.md files in the ``examples/`` directory.

In both examples we follow the same file structure with three key files:
1. ``{game}_callback.py``: This file defines how we collect data using hooks in the app.
2. ``{game}_*_server.py``: This file launches the app for a particular experiment.
3. ``{game}_utils.py``: In the utils file, we define the process by which we render objects in the browser (e.g., defining a function that specifies sprite relationship, canvas objects, etc.).

Example AI policies as ONNX files are also included in the ``policies/`` directory.

Acknowledgements
---------------------

The Phaser integration and server implementation are inspired by and derived from the 
Overcooked AI demo by Carroll et al. (https://github.com/HumanCompatibleAI/overcooked-demo/tree/master).




Installation
------------
To use Interactive Gym, clone this repository. PyPi coming soon!
