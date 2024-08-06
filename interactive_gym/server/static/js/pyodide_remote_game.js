class RemoteGame {
    constructor(config) {
        this.config = config;
        this.pyodideReady = this.initializePyodide(); 
        this.objects_to_render = [];
        this.observations = [];
        this.render_state = null;
        this.num_episodes = config.num_episodes;
        this.step = -1;
    }

    async initialize() {
        this.pyodide = await loadPyodide();

        await this.pyodide.loadPackage("micropip");
        if (this.config.packages) {
            const micropip = pyodide.pyimport("micropip");
            await micropip.install(this.config.packages);
        }

        // The code executed here should instantiate an environment `env`
        await this.pyodide.runPythonAsync(`
            ${this.config.environment_initialization_code}
        `);

        this.env = this.pyodide.globals.get("env");
        if (this.env === undefined) {
            throw new Error("The environment was not initialized correctly. Ensure the the environment_initialization_code correctly creates an `env` object.");
        }
    }

    async reset() {
        await this.pyodideReady;
        const result = await this.pyodide.runPythonAsync(`
            obs, infos = env.reset()
            render_state = env.env_to_render_fn()
            obs, infos, render_state
        `);
        const [obs, infos, render_state] = this.pyodide.globals.toJs(result);
        this.render_state = render_state;
        this.step = this.step + 1;
        return {obs, infos, render_state}
    }


    async step(actions) {
        await this.pyodideReady;
        const result = await this.pyodide.runPythonAsync(`
            obs, rewards, terminateds, truncateds, infos = env.step(${actions})
            render_state = env.env_to_render_fn()
            obs, rewards, terminateds, truncateds, infos, render_state
        `);
        const [obs, rewards, terminateds, truncateds, infos, render_state] = this.pyodide.globals.toJs(result);
        this.step = this.step + 1;

        // Check if all values in terminates dictionary are true
        const all_terminated = Object.values(terminateds).every(Boolean);
        const all_truncated = Object.values(truncateds).every(Boolean);
        if (all_terminated || all_truncated) {
            this.step = -1;
        }
        this.render_state = render_state;

        return {obs, rewards, terminateds, truncateds, infos, render_state}
    }
}