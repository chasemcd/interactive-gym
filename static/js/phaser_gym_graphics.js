var game_config = {
    type: Phaser.AUTO,
    pixelArt: true,
    audio: {
        noAudio: true
    }
};

var scene_config = {
    width: 600,
    height: 600,
    background: "#FFFFFF",
    assets_loc : "./static/assets/",
};

var game_graphics;

class GraphicsManager {
    constructor(game_config, scene_config, graphics_config) {
        game_config.scene = new GymScene(scene_config);
        game_config.width = scene_config.width;
        game_config.height = scene_config.height;
        game_config.state_init = scene_config.state_init;
        this.game = new Phaser.Game(game_config);
    }

    set_state(state) {
        this.game.scene.getScene('GymScene').state_update(state);
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
    }
 */

class GymScene extends Phaser.Scene {

    constructor(config) {
        super({key: "GymScene"});
        this.object_map = {};
        this.state = config.state_init;
    }
    preload () {
        // TODO
        this.load.image('green_ball', "./static/assets/green_ball.png")
    };

    create() {
        this.drawState(this.state);
    };

    update() {
        // TODO
    };

    drawState(state) {
        // TODO
        for (let game_obj in state) {
            let uuid = game_obj.uuid;

            // Check if we already have this object rendered,
            // if not, add it.
            if (!this.object_map.hasOwnProperty(uuid)) {
                this._addObject(game_obj);
            }

            this._updateObject(game_obj);

        }
    };

    _addObject(object_config) {
        let uuid = object_config.uuid;
        let obj_sprite = this.add.sprite();
        this.object_map[uuid] = obj_sprite;
    };

    _updateObject(object_config) {
        let uuid = object_config.uuid;
        let obj = this.object_map.uuid;
        obj.x = object_config.x;
        obj.y = object_config.y;
        obj.angle = object_config.angle;

    }

}