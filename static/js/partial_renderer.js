class GraphicsManager {
    constructor(game_config, graphics_config) {
        game_config.scene = new RGBScene(graphics_config);
        this.game = new Phaser.Game(game_config);
    }

    set_state(state) {
        // console.log("setting state")
        this.game.scene.getScene('RGBScene').set_state(state);
    }
}

class RGBScene extends Phaser.Scene {
    constructor(config) {
        super({ key: 'RGBScene' });
        this.prevState = null;
        this.state = null;
        this.partialRenderTileSize = config.partialRenderTileSize;
        this.height = config.height;
        this.width = config.width;
    }

    set_state(state) {
        console.log("in set_state: ", state)
        this.prevState = this.state;
        this.state = state;
        this.image = this.add.image(400, 300, 'data:image/png;base64,' + state.state);

        var blob = this.base64ToBlob(state.state, 'image/png');
        var url = URL.createObjectURL(blob);

        this.load.image('gameState', url);
        this.load.once('complete', () => {
            this.gameImage.setTexture('gameState');
            URL.revokeObjectURL(url); // Clean up the URL object
        }, this);
        this.load.start();
    }

    preload() {

        this.load.image('bird', './static/assets/bird.png');

        // this.image = this.add.image(400, 300, 'data:image/png;base64,' + data.state);
        // this.cameras.main.setBackgroundColor('#6c53e6')
        // this.socket = io.connect('http://localhost:8000');
        //
        // // Listen for environment state updates from the server
        // this.socket.on('environment_state', function (data) {
        //     // Create a sprite with the updated environment state
        //     if (this.image) {
        //         this.image.destroy();  // Destroy the previous image if it exists
        //     }
        //     this.image = this.add.image(400, 300, 'data:image/png;base64,' + data.state);
        // }, this);

    }

    create() {
        // console.log("adding image")
        // this.image = this.add.image(400, 300, "bird");

        this.socket = io();
        this.gameImage = this.add.image(400, 300, 'gameImage');

        // this.socket.on('environment_state', (data) => {
        //     console.log("environment_state")
        //     this.load.image('gameState', 'data:image/png;base64,' + data.state);
        //     this.load.once('complete', () => {
        //         this.gameImage.setTexture('gameState');
        //     }, this);
        //     this.load.start();
        // });

    }

    update() {
        // this.socket.on('environment_state', (data) => {
        //     console.log("environment_state")
        //     this.load.image('gameState', 'data:image/png;base64,' + data.state);
        //     this.load.once('complete', () => {
        //         this.gameImage.setTexture('gameState');
        //     }, this);
        //     this.load.start();
        // });

        //         // Listen for environment state updates from the server
        // this.socket.on('environment_state', function (data) {
        //     // Create a sprite with the updated environment state
        //     if (this.image) {
        //         this.image.destroy();  // Destroy the previous image if it exists
        //     }
        //     this.image = this.add.image(400, 300, 'data:image/png;base64,' + data.state);
        // }, this);
        //
        // console.log("logging this.state before updating this.image", this.state)
        // this.image = this.add.image(400, 300, 'data:image/png;base64,' + this.state.state)

        // this.socket.emit('request_state_update');
        //
        // // Listen for image data from the server
        // this.socket.on('process_state_update', function (data) {
        //     console.log(typeof(data))
        //     if (typeof(data) !== 'undefined') {
        //         console.log("updating image")
        //         this.image.setTexture('data:image/png;base64,' + data.state);
        //         this.prevState = this.state;
        //         this.state = data;
        //     }
        // }, this);

        // if (typeof(this.state) !== 'undefined') {
        //     console.log("updating image")
        // }

    }

    // updateState(updateData) {
    //     // this.image.setTexture("data:image/png;base64," + imageData);
    //     // this.game.add.image(400, 300, 'data:image/png;base64,' + this.state);
    // }

}


const game_config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    partialRenderTileSize : 32,
    scene: RGBScene,
};


// Functions for instantiating/tearing down/updating graphics
var graphics;

// Invoked at every state update from server
function updateState(state_data) {
    // Try catch necessary because state pongs can arrive before graphics manager has finished initializing
    try {
        graphics.set_state(state_data);
    } catch {
        console.log("error updating state");
    }
};

// Invoked at 'start_game' event
function graphics_start(graphics_config) {
    graphics = new GraphicsManager(game_config, graphics_config);
};

// Invoked at 'end_game' event
function graphics_end() {
    console.log("graphics end")
    graphics.game.renderer.destroy();
    graphics.game.loop.stop();
    graphics.game.destroy();
}



