Client Side Experiments
=======================

One major benefit of using Interactive Gym is that you can forego reimplementing your simulation
environment in a front-end compatible format. For instance, after building a Gymnasium environment, 
in Python, you'd typically have to reimplement the environment in something like JavaScript for
a web-based experiment. Interactive Gym allows you to skip this step and use the same Python-based
environments for web-based experiments. 

Server-side logic is the easiest way to circumvent the need to reimplement your environment; however,
this approach suffers from the problem that you must transmit your environment's state over the network
for every step of the experiment. This can be very slow if the environment is large or the simulation
is computationally intensive, and is limited by the speed of the network connection.

As an alternative, we can use Pyodide, a Python distribution compatible with web-based JavaScript. Interactive Gym's
client-side experiments use Pyodide to run Python-based environments directly in the client's web browser --- while
also conducting AI inference in the browser (either through Python or JS-compatible models, such as ONNX).



.. warning::
   Client side experiments are limited to a single human participant, although you can use as many AI partners as desired.



In order to use client-side experiments, you must specify the ``run_through_pyodide`` flag when constructing 
the ``GymScene`` and pass into the scene the Python code that initializes your environment. You can also specify
any pure-Python packages required for your environment to run, or links to .whl files to install via Micropip.

.. code-block:: python

    scene = (
        GymScene()
        # [...]
        .pyodide(
            run_through_pyodide=True,
            environment_initialization_code_filepath="path/to/your/environment_initialization.py",
            packages_to_install=["your", "required", "packages", "or", "links", "to", ".whls"],
        )
    )

Several augmentations must be made to the environment class in order to make this work efficiently. 

First, we must augment the environment class to allow for the transmission of its state to the server. This
is done by overriding the ``render`` method to return the environment's state in a format that Interactive Gym
uses to render the scene. The ``render`` method must return a list of objects from Interactive Gym's ``object_contexts`` module.

.. code-block:: python

    class YourEnvironment(ParallelEnv):

        def render(self):
            sprite_1 = Sprite(
                    f"agent-1-sprite",
                    x=x, # x position of the sprite
                    y=y, # y position of the sprite
                    height=TILE_SIZE, # pixel height of the sprite
                    width=TILE_SIZE, # pixel width of the sprite
                    image_name="spritesheet_name",
                    frame=f"frame_in_spritesheet.png",
            )

            sprite_2 = Sprite(
                    f"agent-2-sprite",
                    x=x, # x position of the sprite
                    y=y, # y position of the sprite
                    height=TILE_SIZE, # pixel height of the sprite
                    width=TILE_SIZE, # pixel width of the sprite
                    image_name="spritesheet_name",
                    frame=f"frame_in_spritesheet.png",
            )


            return [sprite_1, sprite_2]
        

Second, we must augment the environment class to allow for the transmission of additional information.
More likely than not, you'll want to log information such as the curent state, rewards, etc. By default,
Interactive Gym will track all data that is returned in the ``infos`` dictionary. Any step-level
information that you'd like to track should be returned in ``infos``.

.. code-block:: python

    def step(self, actions: dict[int, int], **kwargs):
        # All env step logic
        observations = ...
        rewards = ...
        terminateds = ...
        truncateds = ...

        # Add data tracking of the reward by adding the reward to the infos dictionary
        infos = {agent_id: {} for agent_id in self.agent_ids}  
        for agent_id, reward in rewards.items():
            infos[agent_id]["reward"] = reward

        return observations, rewards, terminateds, truncateds, infos
