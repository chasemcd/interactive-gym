// Define configs

const game_config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    partialRenderTileSize : 32,
    scene: EnvironmentRGBScene,
};


// Functions for instantiating/tearing down/updating graphics
var graphics;

// Invoked at every state update from server
function drawState(image) {
    // Try catch necessary because state pongs can arrive before graphics manager has finished initializing
    try {
        graphics.update_image(image);
    } catch {
        console.log("error updating state");
    }
};

// Invoked at 'start_game' event
function graphics_start(graphics_config) {
    graphics = new GraphicsManager(game_config, scene_config);
};

// Invoked at 'end_game' event
function graphics_end() {
    graphics.game.renderer.destroy();
    graphics.game.loop.stop();
    graphics.game.destroy();
}


class GraphicsManager {
    constructor(game_config, scene_config) {
        game_config.scene = new EnvironmentRGBScene(scene_config);
        game_config.parent = graphics_config.container_id;
        this.game = new Phaser.Game(game_config);
    }

    set_state(state) {
        this.game.scene.getScene('PlayGame').set_state(state);
    }
}


class EnvironmentRGBScene extends Phaser.Scene {
    constructor(config) {
        super({ key: 'EnvironmentScene' });
        this.prevImageData = null;
        this.partialRenderTileSize = config.partialRenderTileSize;
        this.height = config.heigh;
        this.width = config.width;
    }

    create() {
        // Create a blank texture to hold the image data
        this.texture = this.textures.createCanvas('envImage', this.height, this.width);
        this.add.image(400, 300, 'envImage');

        // // Connect to the server
        // this.socket = new WebSocket('ws://localhost:12345');
        // this.socket.binaryType = 'arraybuffer';
        // this.socket.onmessage = (event) => {
        //     this.updateImage(event.data);
        // };
    }

    updateImage(imageData) {
        // Convert the ArrayBuffer to a Blob
        let blob = new Blob([new Uint8Array(imageData)], { type: 'image/png' });

        // Create a URL for the Blob and update the texture
        let url = URL.createObjectURL(blob);
        let img = new Image();

        img.onload = () => {
            URL.revokeObjectURL(url);  // Revoke the URL once the texture is loaded

            // Draw the image to a temporary canvas to get image data
            let tempCanvas = document.createElement('canvas');
            tempCanvas.width = img.width;
            tempCanvas.height = img.height;
            let tempCtx = tempCanvas.getContext('2d');
            tempCtx.drawImage(img, 0, 0);

            let currImageData = tempCtx.getImageData(0, 0, img.width, img.height);

            // Assume that this is the first frame if prevImageData is null
            if (!this.prevImageData) {
                this.texture.context.drawImage(img, 0, 0);
                this.texture.refresh();
                this.prevImageData = currImageData;
                return;
            }

            // Compare previous image data to current image data to find changed tiles
            let changedTiles = [];
            for (let y = 0; y < img.height; y += this.tileSize) {
                for (let x = 0; x < img.width; x += this.tileSize) {
                    let tileChanged = this.isTileChanged(x, y, currImageData, this.prevImageData);
                    if (tileChanged) {
                        changedTiles.push({ x, y });
                    }
                }
            }

            // Update only the changed tiles
            for (let tile of changedTiles) {
                this.texture.context.drawImage(tempCanvas, tile.x, tile.y, this.tileSize, this.tileSize, tile.x, tile.y, this.tileSize, this.tileSize);
            }
            this.texture.refresh();

            this.prevImageData = currImageData;
        };

        img.src = url;
    }

    isTileChanged(x, y, currImageData, prevImageData) {
        // Compare the image data of the tile at (x, y) to see if it has changed
        for (let ty = 0; ty < this.tileSize; ty++) {
            for (let tx = 0; tx < this.tileSize; tx++) {
                let index = ((y + ty) * currImageData.width + (x + tx)) * 4;
                if (
                    currImageData.data[index] !== prevImageData.data[index] ||
                    currImageData.data[index + 1] !== prevImageData.data[index + 1] ||
                    currImageData.data[index + 2] !== prevImageData.data[index + 2] ||
                    currImageData.data[index + 3] !== prevImageData.data[index + 3]
                ) {
                    return true;
                }
            }
        }
        return false;
    }
}

