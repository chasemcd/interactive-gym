var socket = io();

$(function() {
    $('#startButton').click( () => {
        $("#startButton").hide();
        $("#startButton").attr("disabled", true);
        socket.emit("join", {session_id: window.sessionId});

    })
})

socket.on('server_session_id', function(data) {
    window.sessionId = data.session_id;
});


socket.on('invalid_session', function(data) {
    alert(data.message);
    $('#finalPageHeaderText').hide()
    $('#finalPageText').hide()
    $("#gameHeaderText").hide();
    $("#gamePageText").hide();
    $("#gameContainer").hide();
    $("#invalidSession").show();
});


socket.on("start_game", function(data) {
    $("#welcomeHeader").hide();
    $("#welcomeText").hide();
    $("#instructions").hide();
    $("#waitroomText").hide();
    $('#errorText').hide()
    $("#gameHeaderText").show();
    $("#gamePageText").show();
    $("#gameContainer").show();

    let config = data.config;

    // Initialize game
    let graphics_config = {
        'parent': 'gameContainer',
        'fps': {
            'target': config.fps,
            'forceSetTimeOut': true
        },
        'height': config.game_height,
        'width': config.game_width,
        'background': config.background,
        'state_init': config.state_init,
        'assets_dir': config.assets_dir,
        'assets_to_preload': config.assets_to_preload,
        'animation_configs': config.animation_configs,
    };

    enable_key_listener(config.input_mode)
    graphics_start(graphics_config);
})

var waitroomInterval;
socket.on("waiting_room", function(data) {
    if (waitroomInterval) {
        clearInterval(waitroomInterval);
    }

    var timer = Math.floor(data.ms_remaining / 1000); // Convert milliseconds to seconds


    // Update the text immediately to reflect the current state
    updateWaitroomText(data, timer);

    // Set up a new interval
    waitroomInterval = setInterval(function () {
        timer--;
        updateWaitroomText(data, timer);

        // Stop the timer if it reaches zero
        if (timer <= 0) {
            clearInterval(waitroomInterval);
            $("#waitroomText").text("Sorry, could not find enough players. You will be redirected shortly...");
            setTimeout(function() {
                socket.emit("leave_game", {session_id: window.sessionId})
            }, 10_000)
        }
    }, 1000);
    $("#waitroomText").show();

})

function updateWaitroomText(data, timer) {
    var minutes = parseInt(timer / 60, 10);
    var seconds = parseInt(timer % 60, 10);

    minutes = minutes < 10 ? "0" + minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;
    $("#waitroomText").text(`There are ${data.cur_num_players} / ${data.cur_num_players + data.players_needed} players in the lobby. Waiting ${minutes}:${seconds} for more to join...`);
}

socket.on("game_reset", function(data) {
    graphics_end()
    $('#hudText').hide()
    disable_key_listener();


    // Initialize game
    let config = data.config;
    let graphics_config = {
        'parent': 'gameContainer',
        'fps': {
            'target': config.fps,
            'forceSetTimeOut': true
        },
        'height': config.game_height,
        'width': config.game_width,
        'background': config.background,
        'state_init': config.state_init,
        'assets_dir': config.assets_dir,
        'assets_to_preload': config.assets_to_preload,
        'animation_configs': config.animation_configs,
    };

    input_mode = config.input_mode;

    startResetCountdown(data.timeout, function() {
        // This function will be called after the countdown
        enable_key_listener(input_mode);
        graphics_start(graphics_config);

        socket.emit("reset_complete", {room: data.room, session_id: window.sessionId});
    });


})


function startResetCountdown(timeout, callback) {
    var timer = Math.floor(timeout / 1000); // Convert milliseconds to seconds


    $("#reset-game").show();
    var minutes = parseInt(timer / 60, 10);
    var seconds = parseInt(timer % 60, 10);
    minutes = minutes < 10 ? "0" + minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;
    $("#reset-game").text("Waiting for the next round to start in " + minutes + ":" + seconds + "...");


    var interval = setInterval(function () {
        timer--;
        if (timer <= 0) {
            clearInterval(interval);
            $("#reset-game").hide();
            if (callback) callback(); // Call the callback function
        } else {
            minutes = parseInt(timer / 60, 10);
            seconds = parseInt(timer % 60, 10);

            minutes = minutes < 10 ? "0" + minutes : minutes;
            seconds = seconds < 10 ? "0" + seconds : seconds;
            $("#reset-game").text("Waiting for the next round to start in " + minutes + ":" + seconds + "...");
        }
    }, 1000);
}

socket.on("create_game_failed", function(data) {
    $("#welcomeHeader").show();
    $("#welcomeText").show();
    $("#instructions").show();
    $("#waitroomText").hide();

     $("#startButton").show();
     $("#startButton").attr("disabled", false);


    let err = data['error']
    $('#errorText').show()
    $('#errorText').text(`Sorry, game creation code failed with error: ${JSON.stringify(err)}. You may try again by pressing the start button.`);
})


socket.on('environment_state', function(data) {
    $('#hudText').show()
    $('#hudText').text(data.hud_text)

    addStateToBuffer(data);
    // Emit pong with timestamp
    socket.emit("pong", { timestamp: Date.now() });
});


var latencyMeasurements = [];
socket.on('pong_response', function(data) {
    var latency = Date.now() - data.timestamp;
    latencyMeasurements.push(latency);

    var maxMeasurements = 50; // limit to last 50 measurements
    if (latencyMeasurements.length > maxMeasurements) {
        latencyMeasurements.shift(); // Remove the oldest measurement
    }

    // Calculate the median
    var medianLatency = calculateMedian(latencyMeasurements);

    // Update the latency (ping) display in the UI
    document.getElementById('latencyValue').innerText = medianLatency;
    document.getElementById('latencyContainer').style.display = 'block'; // Show the latency (ping) display
});

function calculateMedian(arr) {
    const sortedArr = arr.slice().sort((a, b) => a - b);
    const mid = Math.floor(sortedArr.length / 2);
    let median;

    if (sortedArr.length % 2 !== 0) {
        median = sortedArr[mid];
    } else {
        median = (sortedArr[mid - 1] + sortedArr[mid]) / 2;
    }

    // Round to the nearest integer
    median = Math.round(median);

    // Format as a two-digit number
    return median.toString().padStart(3, '0');
}

socket.on('end_game', function(data) {
    // Hide game data and display game-over html
    graphics_end();
    disable_key_listener()
    socket.emit("leave_game", {session_id: window.sessionId})

    $('#finalPageHeaderText').show()
    $('#finalPageText').show()
    $("#gameHeaderText").hide();
    $("#gamePageText").hide();
    $("#gameContainer").hide();


    // Set a timeout for redirection
    setTimeout(function() {
        // Redirect to the specified URL after the timeout
        window.location.href = data.redirect_url;
    }, data.redirect_timeout); // 5000 milliseconds = 5 seconds
});





var pressedKeys = {};

socket.on('request_pressed_keys', function(data) {
    socket.emit('send_pressed_keys', {'pressed_keys': Object.keys(pressedKeys), session_id: window.sessionId});
});

function enable_key_listener(input_mode) {
    $(document).on('keydown', function(event) {

        // If we're using the single keystroke input method, we just send the key when it's pressed.
        // This means no composite actions. 
        if (input_mode == "single_keystroke") {
            socket.emit('send_pressed_keys', {'pressed_keys': Array(event.key), session_id: window.sessionId});
            return;
        }

        // Otherwise, we keep track of the keys that are pressed and send them on request
        if (pressedKeys[event.key]) {
            return; // Key is already pressed, so exit the function
        }

        pressedKeys[event.key] = true; // Add key to pressedKeys when it is pressed
    });

    $(document).on('keyup', function(event) {
        if (input_mode == "single_keystroke") {
            return;
        }

        // If we're tracking pressed keys, remove it
        delete pressedKeys[event.key]; // Remove key from pressedKeys when it is released
    });
}


function disable_key_listener() {
        $(document).off('keydown');
        $(document).off('keyup');
}