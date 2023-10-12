var socket = io();

function startGame() {
    console.log("startGame()!");
    document.getElementById("startBtn").style.display = "none";
    document.getElementById("headerButton").style.display = "none";
    document.getElementById("headerText").style.display = "box";

    let graphics_config = {}; // Should be defined by game attributes
    graphics_start(graphics_config);
}

// socket.on('start_game', (data) => {
//     // graphics_config = some function of data
//     console.log("on start game! starting graphics");
//     graphics_config = {};
// });

socket.on('state_update', function(data) {
    // Draw state update
    drawState(data['state']);
});

socket.on('end_game', function(data) {
    // Hide game data and display game-over html
    graphics_end();
});