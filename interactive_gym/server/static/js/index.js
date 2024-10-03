import {graphics_start, graphics_end, addStateToBuffer, getRemoteGameData} from './phaser_gym_graphics.js';
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
        console.log("joining game in session", window.sessionId)
        socket.emit("join_game", {session_id: window.sessionId});

    })
})

socket.on('server_session_id', function(data) {
    window.sessionId = data.session_id;
});

socket.on('connect', function() {
    console.log("connecting")
    // Emit an event to the server with the subject_id
    socket.emit('register_subject', { subject_id: subjectName });
    $("#invalidSession").hide();
    $('#hudText').hide()


});


socket.on('invalid_session', function(data) {
    alert(data.message);
    // $('#finalPageHeaderText').hide()
    // $('#finalPageText').hide()
    // $("#gameHeaderText").hide();
    // $("#gamePageText").hide();
    $("#gameContainer").hide();
    $("#invalidSession").show();
});

socket.on('start_game', function(data) {
    // Clear the waitroomInterval to stop the waiting room timer
    if (waitroomInterval) {
        clearInterval(waitroomInterval);
    }

    let scene_metadata = data.scene_metadata
    // let experiment_config = data.experiment_config

    // Hide the sceneBody and any waiting room messages or errors
    if (scene_metadata.in_game_scene_body != undefined) {
        $("#sceneBody").html(scene_metadata.in_game_scene_body);
        $("#sceneBody").show();
    } else {
        $("#sceneBody").hide(); 
    }
    $("#waitroomText").hide();
    $('#errorText').hide()

    // Show the game container 
    $("#gameContainer").show();

    // Initialize game
    let graphics_config = {
        'parent': 'gameContainer',
        'fps': {
            'target': scene_metadata.fps,
            'forceSetTimeOut': true
        },
        'height': scene_metadata.game_height,
        'width': scene_metadata.game_width,
        'background': scene_metadata.background,
        'state_init': scene_metadata.state_init,
        'assets_dir': scene_metadata.assets_dir,
        'assets_to_preload': scene_metadata.assets_to_preload,
        'animation_configs': scene_metadata.animation_configs,
        'pyodide_remote_game': pyodideRemoteGame,
        'scene_metadata': scene_metadata,
    };

    ui_utils.enableKeyListener(scene_metadata.input_mode)
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

    let scene_metadata = data.scene_metadata


    // Initialize game
    let graphics_config = {
        'parent': 'gameContainer',
        'fps': {
            'target': scene_metadata.fps,
            'forceSetTimeOut': true
        },
        'height': scene_metadata.game_height,
        'width': scene_metadata.game_width,
        'background': scene_metadata.background,
        'state_init': scene_metadata.state_init,
        'assets_dir': scene_metadata.assets_dir,
        'assets_to_preload': scene_metadata.assets_to_preload,
        'animation_configs': scene_metadata.animation_configs,
        'scene_metadata': scene_metadata,
    };

    input_mode = scene_metadata.input_mode;

    startResetCountdown(data.timeout, function() {
        // This function will be called after the countdown
        ui_utils.enableKeyListener(input_mode);
        graphics_start(graphics_config);

        socket.emit("reset_complete", {room: data.room, session_id: window.sessionId});
    });


})


function startResetCountdown(timeout, callback) {
    var timer = Math.floor(timeout / 1000); // Convert milliseconds to seconds


    $("#resetGame").show();
    var minutes = parseInt(timer / 60, 10);
    var seconds = parseInt(timer % 60, 10);
    minutes = minutes < 10 ? "0" + minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;
    $("#resetGame").text("Waiting for the next round to start in " + minutes + ":" + seconds + "...");


    var interval = setInterval(function () {
        timer--;
        if (timer <= 0) {
            clearInterval(interval);
            $("#resetGame").hide();
            if (callback) callback(); // Call the callback function
        } else {
            minutes = parseInt(timer / 60, 10);
            seconds = parseInt(timer % 60, 10);

            minutes = minutes < 10 ? "0" + minutes : minutes;
            seconds = seconds < 10 ? "0" + seconds : seconds;
            $("#resetGame").text("Waiting for the next round to start in " + minutes + ":" + seconds + "...");
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
    $("#sceneBody").html(data.game_page_text);
    $("#sceneBody").show();
})


// var pressedKeys = {};

socket.on('request_pressed_keys', function(data) {
    socket.emit('send_pressed_keys', {'pressed_keys': Object.keys(ui_utils.pressedKeys), session_id: window.sessionId});
});





//  UPDATED

// var canAdvance = true;
// refreshCanAdvance = setInterval(() => {
//     canAdvance = document.getElemendById("canContinue");
//     // if (canContinue == true) {
//     //          $("#advanceButton").attr("disabled", false);
//     //     } else {
//     //         canContinue.onchange = function() {
//     //             if (canContinue.value == "true") {
//     //                 $("#continueButton").attr("disabled", false);
//     //             } else {
//     //                 $("#continueButton").attr("disabled", true);
//     //             }
//     //         }
//     //     }
// } , 100);



var currentSceneMetadata = {};


socket.on("activate_scene", function(data) {
    console.log("Activating scene", data.scene_id)
    activateScene(data);
});


socket.on("terminate_scene", function(data) {
    if (data.element_ids && data.element_ids.length > 0) {
        let retrievedData = getData(data.element_ids);
        socket.emit("static_scene_data_emission", {data: retrievedData, scene_id: data.scene_id, session_id: window.sessionId});
    }
    
    terminateScene(data);
    console.log("Terminating scene", data.scene_id);
    // Add any cleanup logic here if needed
});


function getData(elementIds) {
    let retrievedData = {};
    elementIds.forEach(id => {
        let element = document.getElementById(id);
        if (element) {
            switch(element.tagName.toLowerCase()) {
                case 'input':
                    switch(element.type.toLowerCase()) {
                        case 'checkbox':
                            retrievedData[id] = element.checked;
                            break;
                        case 'radio':
                            let checkedRadio = document.querySelector(`input[name="${element.name}"]:checked`);
                            retrievedData[id] = checkedRadio ? checkedRadio.value : null;
                            break;
                        case 'range':
                            retrievedData[id] = parseFloat(element.value);
                            break;
                        default:
                            retrievedData[id] = element.value;
                    }
                    break;
                case 'select':
                    retrievedData[id] = Array.from(element.selectedOptions).map(option => option.value);
                    break;
                case 'textarea':
                    retrievedData[id] = element.value;
                    break;
                case 'button':
                    retrievedData[id] = element.textContent;
                    break;
                default:
                    retrievedData[id] = element.textContent;
            }
        } else {
            console.warn(`Element with id '${id}' not found`);
            retrievedData[id] = null;
        }
    });
    return retrievedData;
};


function activateScene(data) {
    console.log(data);
    currentSceneMetadata = data;
    if (data.scene_type == "EndScene" || data.scene_type == "CompletionCodeScene") {
        startEndScene(data);
    } else if (data.scene_type == "GymScene") {
        startGymScene(data);
    } else {
        // Treat all other scenes as static scenes
        startStaticScene(data);
    }
};


function startStaticScene(data) {
    // In the Static and Start scenes, we only show
    // the advanceButton, sceneHeader, and sceneBody
    $("#sceneHeader").show();
    $("#sceneSubHeader").show();

    $("#sceneBody").show();

    $("#advanceButton").attr("disabled", false);
    $("#advanceButton").show();

    $("#sceneHeader").html(data.scene_header);
    $("#sceneSubHeader").html(data.scene_subheader);
    $("#sceneBody").html(data.scene_body);



};

function startEndScene(data) {

    $("#sceneHeader").show();
    $("#sceneSubHeader").show();
    $("#sceneBody").show();

    $("#sceneHeader").html(data.scene_header);
    $("#sceneSubHeader").html(data.scene_subheader);

    $("#sceneBody").html(data.scene_body);
    $("#redirectButton").hide();
    $("#advanceButton").hide();

    if (data.url !== undefined && data.url !== null) {
        $("#redirectButton").show();

        let url = data.url;

        if (data.append_subject_id) {
            url = url + subjectName;
        }

        $("#redirectButton").show();

        $("#redirectButton").on("click", function() {
            // Replace this with the URL you want to redirect to
            redirect_subject(url);
        });
    };

};

function startGymScene(data) {
    enableStartRefreshInterval();

    // First, check if we need to initialize Pyodide
    if (data.run_through_pyodide) {
        initializePyodideRemoteGame(data);
        enableCheckPyodideDone();
    };


    // Set the text that we'll display:
    $("#sceneHeader").html(data.scene_header);
    $("#sceneSubHeader").html(data.scene_subheader);
    $("#sceneBody").html(data.scene_body);


    // Next, we display the startButton, header, and body
    $("#sceneHeader").show();
    $("#sceneSubHeader").show();
    $("#sceneBody").show();
    $("#startButton").show();

};


function terminateScene(data) {
    if (data.scene_type == "EndScene") {
        terminateEndScene(data);
    } else if (data.scene_type == "GymScene") {
        terminateGymScene(data);
    } else {
        // (data.scene_type == "StaticScene" || data.scene_type == "StartScene" || data.scene_type == "EndScene")
        // Treat all other scenes as static scenes
        terminateStaticScene(data);
    }
}

function terminateStaticScene(data) {
    $("#sceneHeader").hide();
    $("#sceneSubHeader").hide();
    $("#sceneBody").hide();

    $("#sceneHeader").html("");
    $("#sceneSubHeader").html("");
    $("#sceneBody").html("");


    $("#advanceButton").hide();
    $("#advanceButton").attr("disabled", true);
}

function terminateGymScene(data) {
    ui_utils.disableKeyListener();
    graphics_end();

    let remoteGameData = getRemoteGameData();
    console.log("emitting data", remoteGameData)
    const binaryData = msgpack.encode(remoteGameData);
    socket.emit("emit_remote_game_data", {data: binaryData, scene_id: data.scene_id, session_id: window.sessionId});

    $("#sceneHeader").show();
    $("#sceneHeader").html("");
    
    $("#sceneSubHeader").show();
    $("#sceneSubHeader").html("");
    
    $("#sceneBody").show();
    $("#sceneBody").html("");
    
    $("#startButton").hide();
    $("#gameContainer").hide();

    $('#hudText').hide()
    $('#hudText').text("")
    $('#hudText').html("")


};


// Button Logic

$(function() {
    $('#advanceButton').click( () => {
        $("#advanceButton").hide();
        $("#advanceButton").attr("disabled", true);
        console.log("Emitting advance_scene")
        socket.emit("advance_scene", {session_id: window.sessionId});
    })
})

// GymScene

async function initializePyodideRemoteGame(data) {
    // Only initialize a new RemoteGame if we don't already have one
    if (pyodideRemoteGame === null || data.restart_pyodide === true) {
        pyodideRemoteGame = new RemoteGame(data);
    } else {
        console.log("Not initializing a new RemoteGame because one already exists");
        await pyodideRemoteGame.reinitialize_environment(data);
    }
    // pyodideRemoteGame = new RemoteGame(data);
};

var checkPyodideDone;
function enableCheckPyodideDone() {
    checkPyodideDone = setInterval(() => {
        if (pyodideRemoteGame !== undefined && pyodideRemoteGame.isDone()) {
            clearInterval(checkPyodideDone);
            clearInterval(refreshStartButton);
            // pyodideRemoteGame = undefined;
            
            // Create and show the countdown popup
            const popup = document.createElement('div');
            popup.style.cssText = `
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 20px 40px;
                border-radius: 10px;
                font-family: Arial, sans-serif;
                font-size: 18px;
                text-align: center;
                z-index: 1000;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            `;
            const gameContainer = document.getElementById('gameContainer');
            gameContainer.style.position = 'relative';
            gameContainer.appendChild(popup);
            
            let countdown = 3;
            const updatePopup = () => {
                popup.innerHTML = `
                    <h2 style="margin-bottom: 10px; color: white;">Done!</h2>
                    <p>Continuing in <span style="font-weight: bold; font-size: 24px;">${countdown}</span> seconds...</p>
                `;
                if (countdown === 0) {
                    gameContainer.removeChild(popup);
                    socket.emit("advance_scene", {session_id: window.sessionId});
                } else {
                    countdown--;
                    setTimeout(updatePopup, 1000);
                }
            };
            updatePopup();
        } 
    }, 100);
}



// Check if we're enabling the start button
var refreshStartButton;
function enableStartRefreshInterval() {
    refreshStartButton = setInterval(() => {
        if (currentSceneMetadata.scene_type !== "GymScene") {
            $("#startButton").hide();
            $("#startButton").attr("disabled", true);
        } else if (maxLatency != null && latencyMeasurements.length > 5 && curLatency > maxLatency) {
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
    }, 500);
}


function redirect_subject(url) {
    window.location.href = url;
};