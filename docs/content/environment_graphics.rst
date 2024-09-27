Environment Graphics
=====================

Interactive Gym provides a number of objects that can be used to render graphics in your experiment. 
These objects are all located in the ``interactive_gym.configurations.object_contexts`` module. In order to minimize 
the information passed between the server and the client --- or between the Pyodide python process and the javascript process --- 
the objects are designed to be as simple as possible. For example, rather than passing around a complicated object like a 
game state, we instead pass around a set of atomic objects that represent the game state and provide minimal information
about what has changed in the environment.

.. automodule:: interactive_gym.configurations.object_contexts
    :members:
    :undoc-members:
    :show-inheritance:
    :noindex: