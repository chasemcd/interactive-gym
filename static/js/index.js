var socket = io();


function startGame() {
    // Hide the start button
    document.getElementById('startButton').style.display = 'none';

    // Show the game container
    document.getElementById('gameContainer').style.display = 'block';

    // Hide the start texts
    document.getElementById('startHeaderText').style.display = 'none';
    document.getElementById('startPageText').style.display = 'none';

    // Show the game texts
    document.getElementById('gameHeaderText').style.display = 'block';
    document.getElementById('gamePageText').style.display = 'block';

    // Initialize game
    let graphics_config = {"parent": "gameContainer"}; // Should be defined by game attributes
    graphics_start(graphics_config);
    socket.emit("create_join", {})
}

// Add event listener to the start button
document.getElementById('startButton').addEventListener('click', startGame);

socket.on('environment_state', function(data) {
    // Draw state update
    updateState(data);
});

socket.on('end_game', function(data) {
    // Hide game data and display game-over html
    graphics_end();
});


var pressedKeys = {};
var shouldSendPressedKeys = false;

socket.on('request_pressed_keys', function(data) {
    socket.emit('send_pressed_keys', {'pressed_keys': Object.keys(pressedKeys)});

    // if (shouldSendPressedKeys) {
    //     console.log("sending pressed keys", Object.keys(pressedKeys))
    //     shouldSendPressedKeys = false;
    // }
});

$(document).on('keydown', function(event) {
    if (pressedKeys[event.key]) {
        return; // Key is already pressed, so exit the function
    }

    pressedKeys[event.key] = true; // Add key to pressedKeys when it is pressed
    // shouldSendPressedKeys = true;
});

$(document).on('keyup', function(event) {
    delete pressedKeys[event.key]; // Remove key from pressedKeys when it is released
    // shouldSendPressedKeys = true;
});


