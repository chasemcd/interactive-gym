# CoGrid Overcooked Example

To use the `cogrid` Overcooked environment, you must `pip install` the environment with:

```
pip install git+https://github.com/chasemcd/cogrid.git
```


### Human-AI Server

To run on `localhost`, use the following command, where `-l` specifies the local IP option:

`./up.sh --module interactive_gym.examples.cogrid_overcooked.overcooked_human_ai_server -n 1 -l`

To run on, e.g., four ports with load balancind and a Redis message queue:

`./up.sh --module interactive_gym.examples.cogrid_overcooked.overcooked_human_ai_server -n 4 -r -b`
