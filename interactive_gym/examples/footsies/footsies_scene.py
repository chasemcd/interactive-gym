from interactive_gym.scenes import unity_scene


class FootsiesScene(unity_scene.UnityScene):
    scene_header = "Footsies"
    scene_subheader = """ 
        <center>
        <p> Press "vs cpu" to begin!</p>
        <p>
        Move left and right with <img src="static/assets/keys/icons8-a-key-50.png" alt="A key" height="24" width="24" style="vertical-align:middle;"> and <img src="static/assets/keys/icons8-d-key-50.png" alt="A key" height="24" width="24" style="vertical-align:middle;">
        and use the space bar <img src="static/assets/keys/icons8-space-key-50.png" alt="A key" height="24" width="24" style="vertical-align:middle;"> to attack!
        </p>
        </center>
    """

    def __init__(self):
        super().__init__()
        self.build_name = "footsies_webgl_0224"
        self.height = 1080 / 3
        self.width = 1960 / 3
