class RemoteGame {
    constructor(config) {
        this.config = config;
        this.micropip = null;
        this.pyodideReady = false;
        this.initialize(); 
        this.objects_to_render = [];
        this.observations = [];
        this.render_state = null;
        this.num_episodes = config.num_episodes;
        this.step_num = 0;
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

        // The code executed here must instantiate an environment `env`
        const env = await this.pyodide.runPythonAsync(`
${this.config.environment_initialization_code}
env
        `);

        if (env == undefined) {
            throw new Error("The environment was not initialized correctly. Ensure the the environment_initialization_code correctly creates an `env` object.");
        }

        this.pyodideReady = true;
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
        render_state = {
            "game_state_objects": render_state.map(item => convertUndefinedToNull(item))
        };
        this.step_num = this.step_num + 1;
        this.shouldReset = false;
        return [obs, infos, render_state]
    }


    async step(actions) {
        // await this.pyodideReady;
        const pyActions = this.pyodide.toPy(actions);
        const result = await this.pyodide.runPythonAsync(`
actions = {int(k): v for k, v in ${pyActions}.items()}
obs, rewards, terminateds, truncateds, infos = env.step(actions)
render_state = env.env_to_render_fn()
obs, rewards, terminateds, truncateds, infos, render_state
        `);

        // Convert everything from python objects to JS objects
        let [obs, rewards, terminateds, truncateds, infos, render_state] = this.pyodide.toPy(result).toJs();
        
        this.step_num = this.step_num + 1;

        render_state = {
            "game_state_objects": render_state.map(item => convertUndefinedToNull(item))
        };


        // Check if the episode is complete
        const all_terminated = Array.from(terminateds.values()).every(value => value === true);
        const all_truncated = Array.from(truncateds.values()).every(value => value === true);

        if (all_terminated || all_truncated) {
            this.shouldReset = true;
        }

        return [obs, rewards, terminateds, truncateds, infos, render_state]
    };
};



// Helper function to convert Proxy(Map) to a plain object
function convertProxyToObject(obj) {
    if (obj instanceof Map) {
        return Array.from(obj).reduce((acc, [key, value]) => {
            acc[key] = value instanceof Object ? this.convertProxyToObject(value) : value;
            return acc;
        }, {});
    } else if (obj instanceof Object) {
        return Object.keys(obj).reduce((acc, key) => {
            acc[key] = obj[key] instanceof Object ? this.convertProxyToObject(obj[key]) : obj[key];
            return acc;
        }, {});
    }
    return obj; // Return value directly if it's neither Map nor Object
}


// Helper function to convert all `undefined` values in an object to `null`
function convertUndefinedToNull(obj) {
    if (typeof obj !== 'object' || obj === null) {
        // Return the value as is if it's not an object or is already null
        return obj;
    }

    for (let key in obj) {
        if (obj[key] === undefined) {
            obj[key] = null; // Convert undefined to null
        } else if (typeof obj[key] === 'object') {
            // Recursively apply the conversion to nested objects
            obj[key] = convertUndefinedToNull(obj[key]);
        }
    }

    return obj;
}