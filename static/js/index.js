var socket = io();

function startGame() {
    console.log("startGame()!");
    document.getElementById("startBtn").style.display = "none";
    document.getElementById("headerButton").style.display = "none";
    document.getElementById("headerText").style.display = "box";

    let graphics_config = {}; // Should be defined by game attributes
    graphics_start(graphics_config);
    socket.emit("create_join", {})
}

socket.on('environment_state', function(data) {
    // console.log("updating state")
    // Draw state update
    updateState(data);
});

socket.on('end_game', function(data) {
    // Hide game data and display game-over html
    graphics_end();
});