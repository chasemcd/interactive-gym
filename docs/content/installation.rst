Installation
============

Interactive Gym requires Python 3.8 or higher and can be installed via pip.

Prerequisites
-------------

Before installing Interactive Gym, ensure you have:

- Python 3.8 or higher
- pip (Python package installer)
- A modern web browser (Chrome, Firefox, Safari, or Edge)

Installation
------------

When building experiments, always install Interactive Gym with the server option:

.. code-block:: bash

    pip install interactive-gym[server]

This installs all dependencies needed to create and host experiments:

- **Core dependencies:**

  - ``gymnasium==1.0.0`` - Standard environment interface
  - ``numpy`` - Numerical computing

- **Server dependencies:**

  - ``eventlet`` - Asynchronous networking
  - ``flask`` - Web framework
  - ``flask-socketio`` - Real-time bidirectional communication
  - ``msgpack`` - Efficient data serialization
  - ``pandas`` - Data logging and export
  - ``flatten_dict`` - Data structure utilities

.. note::

   The base installation (``pip install interactive-gym``) without ``[server]`` only installs the minimal core dependencies (``gymnasium`` and ``numpy``). This minimal version is automatically installed by Pyodide in the participant's browser when running client-side experiments. **As an experiment developer, you should always use the ``[server]`` option.**

Development Installation
------------------------

To contribute to Interactive Gym or modify the source code, clone the repository and install in editable mode:

.. code-block:: bash

    git clone https://github.com/chasemcd/interactive-gym.git
    cd interactive-gym
    pip install -e .

For development with server dependencies:

.. code-block:: bash

    pip install -e ".[server]"

Verify Installation
-------------------

Verify that Interactive Gym is installed correctly:

.. code-block:: python

    import interactive_gym

    # Check that core modules are available
    from interactive_gym.scenes import gym_scene, static_scene, stager
    from interactive_gym.configurations import experiment_config
    from interactive_gym.server import app

    print("Installation successful!")

You should see the message printed without any import errors.

To verify the full installation works, proceed to the :doc:`quick_start` guide where you'll create and run a complete working experiment.

Important: Eventlet Monkey Patching
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All experiment files must include eventlet monkey patching at the very top, before any other imports:

.. code-block:: python

    from __future__ import annotations

    import eventlet

    eventlet.monkey_patch()

    # Now import Interactive Gym and other modules
    from interactive_gym.server import app
    from interactive_gym.scenes import stager, static_scene, gym_scene
    # ... rest of your imports

This monkey patching must occur before importing any other modules to ensure proper asynchronous networking behavior. Without it, your experiments may not work correctly.

Common Installation Issues
--------------------------

**ImportError: No module named 'interactive_gym'**

Ensure you've activated the correct Python environment and that pip installed the package successfully:

.. code-block:: bash

    pip show interactive-gym

**Module 'eventlet' has no attribute 'monkey_patch'**

This usually indicates an outdated version of eventlet. Update it:

.. code-block:: bash

    pip install --upgrade eventlet

**Port already in use**

If port 8000 is already in use, you can specify a different port:

.. code-block:: python

    experiment_config.hosting(port=8080)

Platform-Specific Notes
-----------------------

macOS
^^^^^

On macOS, you may need to install Xcode Command Line Tools if you encounter compilation errors:

.. code-block:: bash

    xcode-select --install

Windows
^^^^^^^

On Windows, if you encounter issues with eventlet, consider using Windows Subsystem for Linux (WSL) or installing via conda:

.. code-block:: bash

    conda install -c conda-forge interactive-gym

Linux
^^^^^

On Linux systems, you may need to install system dependencies for some optional features:

.. code-block:: bash

    # Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install python3-dev build-essential

Virtual Environments
--------------------

We strongly recommend using a virtual environment to avoid dependency conflicts:

Using venv (built-in)
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    python -m venv interactive-gym-env
    source interactive-gym-env/bin/activate  # On Windows: interactive-gym-env\Scripts\activate
    pip install interactive-gym

Using conda
^^^^^^^^^^^

.. code-block:: bash

    conda create -n interactive-gym python=3.11
    conda activate interactive-gym
    pip install interactive-gym

Next Steps
----------

Now that you have Interactive Gym installed, you can:

1. Follow the :doc:`quick_start` to create your first experiment
2. Explore the :doc:`tutorials/basic_single_player` for a complete walkthrough
3. Check out the :doc:`examples/index` to see what's possible

For questions or issues, visit the `GitHub repository <https://github.com/chasemcd/interactive-gym>`_ or open an issue.
