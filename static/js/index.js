const canvas = document.querySelector('canvas')
const c = canvas.getContext('2d')
var socket = io();
let pathName = document.location.pathname;
let action = null;
let userID = pathName.substring(pathName.lastIndexOf('/') + 1, pathName.length);

// Event Listeners
canvas.addEventListener("keydown", (event) => {
    if (event.isComposing || event.keyCode === 229) {
        console.log("Ignoring composite or 229 key:", event.key)
        return;
    }
    handleKeyStroke(event);
});

canvas.addEventListener('keyup', () => {
    action = null; // Reset action to null when the key is released
});

document.querySelector("canvas").onblur = function () {
    let me = this;
    setTimeout(function () {
        me.focus();
    }, 500);
}

function startGame() {
    document.getElementById("startBtn").style.display = "none";
    document.getElementById("headerButton").style.display = "none";
    document.getElementById("headerText").style.display = "box";
    init();
    animate();
}

function init() {
    canvas.focus();
    socket.emit("create_join", {});
}

const LEFT = 37;
const RIGHT = 39;
const UP = 38;
const Q_ = 81
const W_ = 87
const E_ = 69;
const SPACE = 32;

function handleKeyStroke(event) {
    //console.log(event.keyCode);
    // console.log(event.key)
    action = event.key
    let action = null;
    switch (event.keyCode) {
        case LEFT: {
            action = "left";
            break;
        }
        case RIGHT: {
            action = "right";
            break;
        }
        case UP: {
            action = "up";
            break;
        }
        case Q_: {
            action = "q";
            break;
        }
        case W_: {
            action = "w";
            break;
        }
        case E_: {
            action = "e";
            break;
        }
        case SPACE: {
            action = "space";
            break;
        }
        default:
            action = null;
    }
    if (action != null) {
        console.log(`Sending action: ${action}`)
        socket.emit("action", {action: action, step: CURRENT_STEP_COUNT});
    }
}


let EPISODE_COUNTER = 0;
socket.on('game_episode_start', function (data) {
    EPISODE_COUNTER++;
    document.getElementById('episodeNum').innerText = "Episode " + EPISODE_COUNTER;
})
socket.on('game_ended', function (data) {
    let url = data.url;
    document.getElementById('episodeNum').innerText = "Game over. You will be redirected shortly ..."
    setTimeout(function () {
        window.location.href = url;
    }, 3000)
})
let CURRENT_STEP_COUNT = 0;
socket.on('game_board_update', function (data) {
    lastImageToDraw = new Image();
    lastImageToDraw.src = "data:image/png;base64," + data.state;
    document.getElementById('footerInfo').textContent = data.rewards;
    CURRENT_STEP_COUNT = data.step;

});
//other game initiated

let lastImageToDraw = null;

// Animation Loop

function animate() {
    requestAnimationFrame(animate)
    //c.clearRect(0, 0, canvas.width, canvas.height)
    if (lastImageToDraw != null) {
        c.drawImage(lastImageToDraw, 0, 0);
        lastImageToDraw = null;
    }
}

//init();