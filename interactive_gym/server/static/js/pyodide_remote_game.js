class RemoteGame {
    constructor(config) {
        this.config = config;
        this.micropip = null;
        this.pyodideReady = this.initialize(); 
        this.objects_to_render = [];
        this.observations = [];
        this.render_state = null;
        this.num_episodes = config.num_episodes;
        this.step_num = -1;
        this.shouldReset = true;
    }

    async initialize() {
        this.pyodide = await loadPyodide();

        await this.pyodide.loadPackage("micropip");
        this.micropip = this.pyodide.pyimport("micropip");

        if (this.config.packages_to_install !== undefined) {
            console.log("Installing packages via micropip: ", this.config.packages_to_install);
            await this.micropip.install(this.config.packages_to_install);
        }

//         // The code executed here should instantiate an environment `env`
        this.env = await this.pyodide.runPythonAsync(`
${this.config.environment_initialization_code}
env
        `);

        if (this.env === undefined) {
            throw new Error("The environment was not initialized correctly. Ensure the the environment_initialization_code correctly creates an `env` object.");
        }
    }

    async reset() {
        await this.pyodideReady;
        this.shouldReset = false;
        const result = await this.pyodide.runPythonAsync(`
obs, infos = env.reset()
render_state = env.env_to_render_fn()
obs, infos, render_state
        `);
        let [obs, infos, render_state] = this.pyodide.toPy(result).toJs();
        render_state = {"game_state_objects": render_state};
        this.step_num = this.step_num + 1;
        return [obs, infos, render_state]
    }


    async step(actions) {
        // await this.pyodideReady;
        console.log("stepping with actions", actions);
        const pyActions = this.pyodide.toPy(actions);
        const result = await this.pyodide.runPythonAsync(`
actions = {int(k): v for k, v in ${pyActions}.items()}
obs, rewards, terminateds, truncateds, infos = env.step(actions)
render_state = env.env_to_render_fn()
obs, rewards, terminateds, truncateds, infos, render_state
        `);
        let [obs, rewards, terminateds, truncateds, infos, render_state] = this.pyodide.toPy(result).toJs();
        this.step_num = this.step_num + 1;

        // Convert everything from python objects to JS objects
        console.log(render_state);
        render_state = {"game_state_objects": render_state};

        // Check if all values in terminates dictionary are true
        const all_terminated = Object.values(terminateds).every(Boolean);
        const all_truncated = Object.values(truncateds).every(Boolean);
        console.log("Terminateds: ", terminateds, "Truncateds: ", truncateds, "All Terminated: ", all_terminated, "All Truncated: ", all_truncated);
        if (all_terminated || all_truncated) {
            this.shouldReset = true;
        }

        return [obs, rewards, terminateds, truncateds, infos, render_state]
    }
}