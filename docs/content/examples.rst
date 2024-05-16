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


.. code-block:: python
    
    config = RemoteConfig()


Below we walk step-by-step through each component of the the Interactive Gym ``RemoteConfig`` for Slime Volleyball.
First, for the environment instantiation, we must define the ``env_creator`` function, which is called to 
return an instance of the environment. 
.. code-block:: python

    def env_creator(*args, **kwargs):
        config = {"human_inputs": True}
        return slimevolley_env.SlimeVolleyEnv(config=config)
 
    config.environment(
        env_creator=env_creator
    )






CoGrid Overcooked
------------------



