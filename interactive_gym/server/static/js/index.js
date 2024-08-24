import {graphics_start, graphics_end, addStateToBuffer} from './phaser_gym_graphics.js';
import {RemoteGame} from './pyodide_remote_game.js';
import * as ui_utils from './ui_utils.js';

var socket = io();
var start_pressed = false;



var latencyMeasurements = [];
var curLatency;
var maxLatency;


var pyodideRemoteGame = null;

var documentInFocus = false;
document.addEventListener("visibilitychange", function() {
  if (document.hidden) {
    documentInFocus = false;
    // alert("Please return to the game tab to avoid interruptions and to facilitate a good experience for all players.");
  } else {
    documentInFocus = true;
  }
});

window.addEventListener('focus', function() {
    // The window has gained focus
    documentInFocus = true;
});

window.addEventListener('blur', function() {
    // The window has lost focus
    documentInFocus = false;
});

socket.on('pong', function(data) {
    var latency = Date.now() - window.lastPingTime;
    latencyMeasurements.push(latency);

    var maxMeasurements = 20; // limit to last 50 measurements
    if (latencyMeasurements.length > maxMeasurements) {
        latencyMeasurements.shift(); // Remove the oldest measurement
    }

    // Calculate the median
    var medianLatency = calculateMedian(latencyMeasurements);

    // Update the latency (ping) display in the UI
    document.getElementById('latencyValue').innerText = medianLatency.toString().padStart(3, '0');
    document.getElementById('latencyContainer').style.display = 'block'; // Show the latency (ping) display
    curLatency = medianLatency;
    maxLatency = data.max_latency;
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
    return median;
}


function sendPing() {
    window.lastPingTime = Date.now();
    socket.emit('ping', {ping_ms: curLatency, document_in_focus: documentInFocus});
}

// Send a ping every second
setInterval(sendPing, 1000);

// Check if we're enabling the start button
var refreshStartButton = setInterval(() => {
    if (maxLatency != null && latencyMeasurements.length > 5 && curLatency > maxLatency) {
        $("#instructions").hide();
        $("#startButton").hide();
        $("#startButton").attr("disabled", true);
        $('#errorText').show()
        $('#errorText').text("Sorry, your connection is too slow for this application. Please make sure you have a strong internet connection to ensure a good experience for all players in the game.");
        clearInterval(refreshStartButton);
    } else if (maxLatency != null && latencyMeasurements.length <= 5) {
        $("#startButton").show();
        $("#startButton").attr("disabled", true);
    } 
    else if (pyodideReadyIfUsing()){
        $('#errorText').hide()
        $("#startButton").show();
        $("#startButton").attr("disabled", false);
        clearInterval(refreshStartButton);
    }
}, 1000)

function pyodideReadyIfUsing() {
    if (pyodideRemoteGame == null) {
        console.log("pyodideRemoteGame is null")
        return true;
    }

    console.log(pyodideRemoteGame.pyodideReady)
    return pyodideRemoteGame.pyodideReady;
}


$(function() {
    $('#startButton').click( () => {
        $("#startButton").hide();
        $("#startButton").attr("disabled", true);
        start_pressed = true;
        socket.emit("join", {session_id: window.sessionId});

    })
})

socket.on('server_session_id', function(data) {
    window.sessionId = data.session_id;
});

socket.on('connect', function() {
    // Emit an event to the server with the subject_name
    socket.emit('register_subject_name', { subject_name: subjectName });
    socket.emit('request_pyodide_initialization', {});
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
    // Clear the waitroomInterval to stop the waiting room timer
    if (waitroomInterval) {
        clearInterval(waitroomInterval);
    }

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
        'interactive_gym_config': config,
    };

    ui_utils.enableKeyListener(config.input_mode)
    graphics_start(graphics_config);
})


socket.on('initialize_pyodide_remote_game', function(data) {
    pyodideRemoteGame = new RemoteGame(data.config);
});


socket.on('start_game_pyodide', function(data) {
    // Clear the waitroomInterval to stop the waiting room timer
    if (waitroomInterval) {
        clearInterval(waitroomInterval);
    }

    $("#welcomeHeader").hide();
    $("#welcomeText").hide();
    $("#instructions").hide();
    $("#waitroomText").hide();
    $('#errorText').hide()
    $("#gameHeaderText").show();
    $("#gamePageText").show();
    $("#gameContainer").show();

    let config = data.config;
    // let pyodideRemoteGame = new RemoteGame(data.config);

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
        'pyodide_remote_game': pyodideRemoteGame,
        'interactive_gym_config': config,
    };

    ui_utils.enableKeyListener(config.input_mode)
    graphics_start(graphics_config);
});


var waitroomInterval;
socket.on("waiting_room", function(data) {
    if (waitroomInterval) {
        clearInterval(waitroomInterval);
    }

    $("#instructions").hide();


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
            console.log("Leaving game due to waitroom ending...")
            socket.emit("leave_game", {session_id: window.sessionId})
            socket.emit('end_game_request_redirect', {waitroom_timeout: true})
        }
    }, 1000);
    $("#waitroomText").show();

})


var singlePlayerWaitroomInterval;
socket.on("single_player_waiting_room", function(data) {
    if (singlePlayerWaitroomInterval) {
        clearInterval(singlePlayerWaitroomInterval);
    }


    $("#instructions").hide();


    var simulater_timer = Math.floor(data.ms_remaining / 1000); // Convert milliseconds to seconds
    var single_player_timer = Math.floor(data.wait_duration_s); // already in second

    // Update the text immediately to reflect the current state
    updateWaitroomText(data, simulater_timer);

    // Set up a new interval
    singlePlayerWaitroomInterval = setInterval(function () {
        simulater_timer--;
        single_player_timer--;
        updateWaitroomText(data, simulater_timer);

        if (single_player_timer <= 0) {
            clearInterval(singlePlayerWaitroomInterval);
            socket.emit('single_player_waiting_room_end', {})
        }

        // // Stop the timer if it reaches zero
        // if (simulater_timer <= 0) {
        //     clearInterval(singlePlayerWaitroomInterval);
        //     $("#waitroomText").text("Sorry, could not find enough players. You will be redirected shortly...");
        //     console.log("Single player waitroom timed out!")
        //     socket.emit("leave_game", {session_id: window.sessionId})
        //     socket.emit('end_game_request_redirect', {waitroom_timeout: true})
        // }
    }, 1000);
    $("#waitroomText").show();

})


socket.on("single_player_waiting_room_failure", function(data) {

    $("#waitroomText").text("Sorry, you were matched with a player but they disconnected before the game could start. You will be redirected shortly...");
    console.log("Leaving game due to waiting room failure (other player left)...")
    socket.emit("leave_game", {session_id: window.sessionId})
    socket.emit('end_game_request_redirect', {waitroom_timeout: true})

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
    ui_utils.disableKeyListener();


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
        ui_utils.enableKeyListener(input_mode);
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
});





socket.on('end_game', function(data) {
    console.log("game ended!")
    // Hide game data and display game-over html
    graphics_end();
    $('#hudText').hide();
    ui_utils.disableKeyListener();
    socket.emit("leave_game", {session_id: window.sessionId});

    $('#finalPageHeaderText').show()
    $('#finalPageText').show()
    $("#gameHeaderText").hide();
    $("#gamePageText").hide();
    $("#gameContainer").hide();

    if (data.message != undefined) {
        $('#errorText').text(data.message);
        $('#errorText').show();
    }



    socket.emit('end_game_request_redirect', {waitroom_timeout: false})
});


socket.on('end_game_redirect', function(data) {
    console.log("received redirect")
    setTimeout(function() {
        // Redirect to the specified URL after the timeout
        window.location.href = data.redirect_url;
    }, data.redirect_timeout);
});


socket.on('update_game_page_text', function(data) {
    // $("#gamePageText").text(data.game_page_text);
    document.getElementById('gamePageText').innerHTML = data.game_page_text;
})


// var pressedKeys = {};

socket.on('request_pressed_keys', function(data) {
    socket.emit('send_pressed_keys', {'pressed_keys': Object.keys(ui_utils.pressedKeys), session_id: window.sessionId});
});