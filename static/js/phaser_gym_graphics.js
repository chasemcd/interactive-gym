var game_config = {
    type: Phaser.AUTO,
    pixelArt: true,
    audio: {
        noAudio: true
    }
};

var scene_config = {
    width: 600,
    height: 400,
    background: "#FFFFFF",
    assets_dir : "./static/assets/",
    state_init: [],
    assets_to_preload: [],
    animation_configs: [],
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
    // TODO: pass scene config as an argument here.
    game_graphics = new GraphicsManager(game_config, scene_config, graphics_config);
}

class GraphicsManager {
    constructor(game_config, scene_config, graphics_config) {
        game_config.scene = new GymScene(scene_config);
        game_config.width = scene_config.width;
        game_config.height = scene_config.height;
        game_config.background = scene_config.background;
        game_config.state_init = scene_config.state_init;
        game_config.assets_dir = scene_config.assets_dir;
        game_config.assets_to_preload = scene_config.assets_to_preload;
        game_config.animation_configs = scene_config.animation_configs;
        game_config.parent = graphics_config.parent;
        this.game = new Phaser.Game(game_config);
    }

    set_state(state) {
        this.game.scene.getScene('GymScene').set_state(state);

        this.game.scale.pageAlignHorizontally = true;
        this.game.scale.pageAlignVertically = true;
        this.game.scale.refresh();
    }
}


/*
game object dict
    {
        uuid: unique identifier
        image_loc: path to image
        sprite_sheet_loc: path to sprite sheet (if any)
        object_type: object type, if not using an image
        object_size: size of the object
        x: relative x position [0, 1], multiplied by screen width
        y: relative y position [0, 1], multiplied by screen height
        orientation: direction facing (if applicable/using sprite sheet)
        angle: should we rotate the sprite? In degrees.
        depth: object depth (other things render on top?).
        animation: name of the animation to play from a sprite sheet
        animations: a list of animations to initialize from the sprite sheet
                format: anim = {key, frames, frameRate, repeat, hideOnComplete}
    }
 */

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

        // If we don't have any object contexts, we render the image from `env.render()`
        if (game_state_objects == null) {
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


        } else {
            game_state_objects.forEach((game_obj) => {
                let uuid = game_obj.uuid;

                // Check if we need to add a new Sprite
                if (!this.object_map.hasOwnProperty(uuid)) {
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
        }else {
            console.warn("Unrecognized object type in _addObject:", object_config.object_type)
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
        // TODO
    }

    _updateCircle(circle_config) {
        // TODO
    }

    _addRectangle(rectangle_config) {
        // TODO
    }

    _updateRectangle(rectangle_config) {
        // TODO
    }

    _addPolygon(polygon_config) {
        // TODO
    }

    _updatePolygon(polygon_config) {
        // TODO
    }

    _checkIfHex(string_to_test) {
        var reg = /^#[0-9A-F]{6}[0-9a-f]{0,2}$/i
        return reg.test(string_to_test)
    }

    _strToHex(color_str) {
        return parseInt(color_str.replace(/^#/, ''), 16)
    }

}