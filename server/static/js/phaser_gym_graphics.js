var game_config = {
    type: Phaser.AUTO,
    pixelArt: true,
    audio: {
        noAudio: true
    },
    resolution: window.devicePixelRatio,
};

var game_graphics;

function updateState(state_data) {
    try {
        game_graphics.set_state(state_data);
    } catch {
        console.warn("Error updating state; the graphics likely haven't been loaded yet.");
    }
}


function graphics_start(graphics_config) {
    game_graphics = new GraphicsManager(game_config, graphics_config);
}

// Invoked at 'end_game' event
function graphics_end() {
    $("#gameContainer").empty();
    game_graphics.game.renderer.destroy();
    game_graphics.game.loop.stop();
    game_graphics.game.destroy();
}

class GraphicsManager {
    constructor(game_config, graphics_config) {
        game_config.scene = new GymScene(graphics_config);
        game_config.location_representation = graphics_config.location_representation;
        game_config.width = graphics_config.width;
        game_config.height = graphics_config.height;
        game_config.background = graphics_config.background;
        game_config.state_init = graphics_config.state_init;
        game_config.assets_dir = graphics_config.assets_dir;
        game_config.assets_to_preload = graphics_config.assets_to_preload;
        game_config.animation_configs = graphics_config.animation_configs;
        game_config.parent = graphics_config.parent;
        game_config.fps = graphics_config.fps;
        this.game = new Phaser.Game(game_config);
    }

    set_state(state) {
        this.game.scene.getScene('GymScene').set_state(state);

        this.game.scale.pageAlignHorizontally = true;
        this.game.scale.pageAlignVertically = true;
        this.game.scale.refresh();
    }

    set_config
}


class GymScene extends Phaser.Scene {

    constructor(config) {
        super({key: "GymScene"});
        this.object_map = {};
        this.state = config.state_init;
        this.assets_dir = config.assets_dir;
        this.assets_to_preload = config.assets_to_preload;
        this.animation_configs = config.animation_configs;
        this.background = config.background;
    }
    preload () {
        // preload any specified images/assets
        // for (let image_name in this.assets_to_preload) {
        //     this.load.image(image_name, `${this.assets_dir}${image_name}`)
        // }
        //
        // // Define any animations that we might use on our sprites
        // for (let anim in this.animation_configs) {
        //     this.anims.add(
        //          {
        //              key: anim.key,
        //              frames: anim.frames,
        //              frameRate: anim.frameRate,
        //              repeat: anim.repeat,
        //              hideOnComplete: anim.hideOnComplete,
        //          }
        //      )
        // }
    };

    create() {
        // Store the canvas, width, and height for easy access
        this.canvas = this.sys.game.canvas;
        this.canvas.id = "phaser-canvas";
        this.height = this.canvas.height;
        this.width = this.canvas.width;

        // Check if the background is just a color, if so fill
        if (this._checkIfHex(this.background)) {
            this.cameras.main.setBackgroundColor(this._strToHex(this.background));
        } else {
            // If the background isn't a color, load the specified image
            this._addTexture(this.background);
            this.add.image(this.height / 2, this.width / 2, this.background);
        }

        // Draw the initial state, if anything
        this.drawState();
    };

    update() {
        this.drawState();
    };

    set_state(state) {
        this.state = state;
    }

    drawState() {
        /*
        Iterate over the objects defined in the state and
        add them to the environment and update as necessary.
         */

        // Retrieve the list of object contexts
        let game_state_objects = this.state.state;
        let game_state_image = this.state.game_image_base64;

        // If we don't have any object contexts, we render the image from `env.render()`
        // NOTE: This approach is very inefficient and not good practice! It's oriented
        //  to testing or local experiments.
        if (game_state_objects == null && !(game_state_image == null)) {
            // Remove the current image
            let oldImage;

            if (this.object_map.hasOwnProperty("curStateImage")) {
                oldImage = this.object_map['curStateImage'];
            }

            // This will trigger when the new texture is added
            this.textures.once('addtexture', function () {

                // Place the updated image and store so we can remove later
                this.object_map['curStateImage'] = this.add.image(
                    0,
                    0,
                    `curStateImage_${this.state.step}`
                );
                this.object_map['curStateImage'].setOrigin(0, 0);

                // Remove the old image
                if (!(oldImage == null)) {
                    oldImage.destroy();
                }

            }, this);

            // Load the new image
            var base64String = 'data:image/png;base64,' + this.state.game_image_base64; // Replace with your actual Base64 string

            // Success here will trigger the `addtexture` callback
            this.textures.addBase64(`curStateImage_${this.state.step}`, base64String);


        } else if (!(game_state_objects == null)) {
            // If we have game state objects, we'll render and update each object as necessary.
            game_state_objects.forEach((game_obj) => {

                // Check if we need to add a new object
                if (!this.object_map.hasOwnProperty(game_obj.uuid)) {
                    this._addObject(game_obj);
                }


                this._updateObject(game_obj);
            })

        }
    };

    _addObject(object_config) {
        if (object_config.object_type === "sprite") {
            this._addSprite(object_config);
        } else if (object_config.object_type === "animation") {
            this._addAnimation(object_config)
        } else if (object_config.object_type === "line") {
            this._addLine(object_config)
        } else if (object_config.object_type === "circle") {
            this._addCircle(object_config)
        } else if (object_config.object_type === "rectangle") {
            this._addRectangle(object_config)
        } else if (object_config.object_type === "polygon") {
            this._addPolygon(object_config)
        } else if (object_config.object_type === "text") {
            this._addText(object_config)
        } else {
            console.warn("Unrecognized object type in _addObject:", object_config.object_type)
        }
    }

    _updateObject(object_config) {
        if (object_config.object_type === "sprite") {
            this._updateSprite(object_config);
        } else if (object_config.object_type === "line") {
            this._updateLine(object_config)
        } else if (object_config.object_type === "circle") {
            this._updateCircle(object_config)
        } else if (object_config.object_type === "rectangle") {
            this._updateRectangle(object_config)
        } else if (object_config.object_type === "polygon") {
            this._updatePolygon(object_config)
        } else if (object_config.object_type === "text") {
            this._updateText(object_config)
        } else {
            console.warn("Unrecognized object type in _updateObject:", object_config.object_type)
        }
    }

    _addSprite(object_config) {
        let uuid = object_config.uuid;

        // Add a blank sprite to the specified location, everything else
        // will be updated in _updateObject
        this.object_map[uuid] = this.add.sprite(
            {
                x: Math.floor(object_config.x * this.width),
                y: Math.floor(object_config.y * this.height),
                depth: object_config.depth,
            }
        );
    };

    _updateSprite(object_config) {
        let uuid = object_config.uuid;
        let obj = this.object_map[uuid];
        obj.x = Math.floor(object_config.x * this.width);
        obj.y = Math.floor(object_config.y * this.height);
        obj.angle = object_config.angle;

        this._addTexture(object_config.image_name)

        // if (object_config.cur_animation !== null && obj.anims.getCurrentKey() !== object_config.cur_animation) {
        //     obj.play(object_config.cur_animation)
        // } else
        if (object_config.image_name !== null && obj.texture.key !== object_config.image_name) {
            obj.setTexture(object_config.image_name)
        }
    }

    _addTexture(texture_name) {
        // Load the asset with the filepath as the ID
        if (texture_name !== null && !this.textures.exists(texture_name)) {
            this.load.image(texture_name, `${this.assets_dir}${texture_name}`)
            this.load.start()
        }
    }

    _addAnimation(anim_config) {
        // TODO: from an animation config, define an animation.
    }

    _addLine(line_config) {
        var graphics = this.add.graphics()
        var points = line_config.points.map((point) => new Phaser.Math.Vector2(point[0] * this.width, point[1] * this.height))

        graphics.setDepth(line_config.depth);

        // Set the line style (width and color)
        graphics.lineStyle(line_config.width, this._strToHex(line_config.color));

        // Draw the curve
        graphics.beginPath();
        graphics.moveTo(points[0].x, points[0].y);

        for (let i = 1; i < points.length; i++) {
            graphics.lineTo(points[i].x, points[i].y);
        }

        graphics.strokePath();

        if (line_config.fill_above === true) {
            var topY = 0;
            graphics.lineTo(points[points.length - 1].x, topY);
            graphics.lineTo(points[0].x, topY);
            graphics.closePath();

            // Fill the closed shape
            graphics.fillStyle(this._strToHex(line_config.color), 1);
            graphics.fillPath();
        }

        if (line_config.fill_below === true) {
            var bottomY = this.height;
            graphics.lineTo(points[points.length - 1].x, bottomY);
            graphics.lineTo(points[0].x, bottomY);
            graphics.closePath();

            // Fill the closed shape
            graphics.fillStyle(this._strToHex(line_config.color), 1);
            graphics.fillPath();
        }


        this.object_map[line_config.uuid] = graphics;
    }

    _updateLine(line_config) {
        // TODO
    }

    _addCircle(circle_config) {
        var graphics = this.add.graphics();
        graphics.setDepth(circle_config.depth);

        // Set the fill style (color and alpha)
        graphics.fillStyle(this._strToHex(circle_config.color), circle_config.alpha); // Red color, fully opaque

        // Draw a filled circle (x, y, radius)
        this.object_map[circle_config.uuid] = graphics.fillCircle(
            circle_config.x * this.width,
            circle_config.y * this.height,
            circle_config.radius,
        );
    }

    _updateCircle(circle_config) {
        let uuid = circle_config.uuid;
        let graphics = this.object_map[uuid];
        graphics.clear();
        this._addCircle(circle_config);
    }

    _addRectangle(rectangle_config) {
        // TODO
    }

    _updateRectangle(rectangle_config) {
        // TODO
    }

    _addPolygon(polygon_config) {
        let graphics = this.add.graphics();
        var points = polygon_config.points.map((point) => new Phaser.Math.Vector2(point[0] * this.width, point[1] * this.height))

        graphics.setDepth(polygon_config.depth);


        // Set the fill style (color and alpha)
        graphics.fillStyle(this._strToHex(polygon_config.color), polygon_config.alpha);

        // Draw the filled polygon
        graphics.fillPoints(points, true); // 'true' to close the polygon

        this.object_map[polygon_config.uuid] = graphics;

    }

    _updatePolygon(polygon_config) {
        let uuid = polygon_config.uuid;
        let graphics = this.object_map[uuid];
        graphics.clear();
        this._addPolygon(polygon_config);
    }

    _addText(text_config) {
        this.object_map[text_config.uuid] = this.add.text(
            text_config.x * this.width,
            text_config.y * this.height,
            text_config.text,
            { fontFamily: text_config.font, fontSize: text_config.size, color: "#000"}
        );
        this.object_map[text_config.uuid].setDepth(1)
    }

    _updateText(text_config) {
        let text = this.object_map[text_config.uuid];
        text.x = text_config.x * this.width;
        text.y = text_config.y * this.height;
        text.setText(text_config.text);
    }

    _checkIfHex(string_to_test) {
        var reg = /^#[0-9A-F]{6}[0-9a-f]{0,2}$/i
        return reg.test(string_to_test)
    }

    _strToHex(color_str) {
        return parseInt(color_str.replace(/^#/, ''), 16)
    }

}