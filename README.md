# Interactive Gym

Interactive Gym is a platform to run experiments with online participants using environments that follow the `gymnasium` API. 


## Examples

Two examples are provided: CoGrid Overcooked and Slime Volleyball. Interactive experiments with humans and AI or human-human pairs can be run, respectively, via the following commands.

CoGrid Overcooked
`python -m examples.cogrid_overcooked.overcooked_human_ai_server`
`python -m examples.cogrid_overcooked.overcooked_human_human_server`

Slime Volleyball
`python -m examples.slime_volleyball.slime_volleyball_human_ai_server`
`python -m examples.slime_volleyball.slime_volleyball_human_human_server`

Instructions for installation can be found in the respective README.md files in the `examples/` directory.s

### Acknowledgements

The Phaser integration and server implementation is inspired by and derived from the Overcooked AI demo by Carroll et al. (https://github.com/HumanCompatibleAI/overcooked-demo/tree/master). 

