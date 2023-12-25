class GraphicsManager {
    constructor(game_config, graphics_config) {
        game_config.scene = new RGBScene(graphics_config);
        this.game = new Phaser.Game(game_config);
    }

    set_state(state) {
        console.log("setting state")
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
        this.prevState = this.state;
        this.state = state;
    }

    preload() {
        // this.cameras.main.setBackgroundColor('#6c53e6')
    }

    create() {
        // Create a blank texture to hold the image data

        // let fill_graphics = this.add.graphics();
        //
        // // Draw a white rectangle
        // fill_graphics.fillStyle(0xFFFFFF, 1);
        // fill_graphics.fillRect(0, 0, this.width, this.height);  // Assumes you want a 100x100 pixel white image
        //
        // // Generate a texture from the graphics object
        // fill_graphics.generateTexture('whiteTexture', 100, 100);

        // this.renderedImage = this.add.image(this.width, this.height, 'whiteTexture');
        // this.texture = this.textures.createCanvas('whiteTexture', this.height, this.width);
        // this.texture = this.textures.createCanvas('envImage', this.height, this.width);  // Assume 800x600 resolution
        // this.add.image(400, 300, 'envImage');
        // graphics = this.add.graphics();
        this.image = this.add.image(400, 300, 'myImage');

    }

    update() {
        if (typeof(this.state) !== 'undefined') {
            console.log("updating image")
            this.updateImage(this.state)
        }
    }

    updateImage(imageData) {
    //
    //     let imageElement = new Image();
    //     imageElement.src = "data:image/png;base64," + imageData;
    //
    //     imageElement.onload = () => {
    //         // Get the context of the canvas texture
    //         // let context = this.texture.getContext();
    //
    //         // Clear the previous contents
    //         this.texture.context.clearRect(0, 0, this.width, this.height);
    //
    //         // Draw the new image onto the canvas
    //         this.texture.context.drawImage(imageElement, 0, 0);
    //
    //         // Refresh the texture
    //         this.texture.refresh();
    // }

        // graphics.clear();
        // this.load.image('myImage', 'data:image/png;base64,' + imageData);
        // this.add.image(400, 300, 'myImage');

        // Convert the ArrayBuffer to a Blob
        // let blob = new Blob([new Uint8Array("data:image/png;base64," + imageData)], { type: 'image/png' });
        //     // Simulate having an image Blob and rendering it during the update function
        // var fileReader = new FileReader();
        // fileReader.onload = function (event) {
        //     var base64data = event.target.result;
        //     this.image.setTexture('myImage', base64data);
        // };
        // fileReader.readAsDataURL(blob);

        // this.image.setTexture("data:image/png;base64," + imageData);
        this.game.add.image(400, 300, 'data:image/png;base64,' + this.state);

        //
        // // Create a URL for the Blob and update the texture
        // let url = URL.createObjectURL(blob);
        // let img = new Image();
        //
        // img.onload = () => {
        //     URL.revokeObjectURL(url);  // Revoke the URL once the texture is loaded
        //
        //     // Draw the image to a temporary canvas to get image data
        //     let tempCanvas = document.createElement('canvas');
        //     tempCanvas.width = img.width;
        //     tempCanvas.height = img.height;
        //     let tempCtx = tempCanvas.getContext('2d');
        //     tempCtx.drawImage(img, 0, 0);
        //
        //     let currImageData = tempCtx.getImageData(0, 0, img.width, img.height);
        //
        //     // Assume that this is the first frame if prevImageData is null
        //     if (!this.prevImageData) {
        //         this.texture.context.drawImage(img, 0, 0);
        //         this.texture.refresh();
        //         this.prevImageData = currImageData;
        //         return;
        //     }
        //
        //     // Compare previous image data to current image data to find changed tiles
        //     let changedTiles = [];
        //     for (let y = 0; y < img.height; y += this.tileSize) {
        //         for (let x = 0; x < img.width; x += this.tileSize) {
        //             let tileChanged = this.isTileChanged(x, y, currImageData, this.prevImageData);
        //             if (tileChanged) {
        //                 changedTiles.push({ x, y });
        //             }
        //         }
        //     }
        //
        //     // Update only the changed tiles
        //     for (let tile of changedTiles) {
        //         this.texture.context.drawImage(tempCanvas, tile.x, tile.y, this.tileSize, this.tileSize, tile.x, tile.y, this.tileSize, this.tileSize);
        //     }
        //     this.texture.refresh();
        //
        //     this.prevImageData = currImageData;
        // };
        //
        // img.src = url;
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
    graphics.game.renderer.destroy();
    graphics.game.loop.stop();
    graphics.game.destroy();
}



