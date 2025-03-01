export function startUnityScene(data) {
    $("#sceneHeader").show();
    $("#sceneSubHeader").show();
    $("#sceneBody").show();
    $("#hudText").show();

    // Insert Unity WebGL container and loader elements
    startUnityGame(data, "gameContainer");

    $("#gameContainer").show();


    $("#advanceButton").attr("disabled", true);
    $("#advanceButton").hide();

    if (data.scene_header) {
        $("#sceneHeader").show().html(data.scene_header);
    } else {
        $("#sceneHeader").hide();
    }
    if (data.scene_subheader) {
        $("#sceneSubHeader").show().html(data.scene_subheader);
    } else {
        $("#sceneSubHeader").hide();
    }
    if (data.scene_body) {
        $("#sceneBody").show().html(data.scene_body);
    } else {
        $("#sceneBody").hide();
    }


    // Initialize or increment the gym scene counter
    if (typeof window.interactiveGymGlobals === 'undefined') {
        window.interactiveGymGlobals = {};
    }

    window.interactiveGymGlobals.unityEpisodeCounter = 0;
    window.interactiveGymGlobals.unityScore = null;
    if (data.score !== null) {
        window.interactiveGymGlobals.unityScore = 0;
    }
    console.log(window.interactiveGymGlobals.unityScore);
    // Update HUD text to show round progress
    // if (data.num_episodes && data.num_episodes > 1) {
    //     const roundText = `Round ${window.interactiveGymGlobals.unityEpisodeCounter + 1}/${data.num_episodes}`;
    //     $("#hudText").html(roundText);
    // }

    let hudText = '';
    if (data.num_episodes && data.num_episodes > 1) {
        hudText += `Round ${window.interactiveGymGlobals.unityEpisodeCounter + 1}/${data.num_episodes}`;
    }
    
    if (window.interactiveGymGlobals.unityScore !== null) {
        if (hudText) hudText += ' | ';
        hudText += `Score: ${window.interactiveGymGlobals.unityScore}`;
    }

    $("#hudText").html(hudText);

}



let unityInstance = null; // Store Unity instance globally

function startUnityGame(config, elementId) {
    $(`#${elementId}`).empty();
    
    $(`#${elementId}`).html(`
    <div id="unity-container" class="unity-desktop">
      <canvas id="unity-canvas" tabindex="-1"></canvas>
      <div id="unity-loading-bar">
        <div id="unity-logo"></div>
        <div id="unity-progress-bar-empty">
          <div id="unity-progress-bar-full"></div>
        </div>
      </div>
      <div id="unity-warning"> </div>
      <div id="unity-footer">
        <div id="unity-webgl-logo"></div>
        <div id="unity-fullscreen-button"></div>
      </div>
    </div>`);

    var canvas = document.querySelector("#unity-canvas");
    var loadingBar = document.querySelector("#unity-loading-bar");
    var progressBarFull = document.querySelector("#unity-progress-bar-full");
    var fullscreenButton = document.querySelector("#unity-fullscreen-button");

    if (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) {
        canvas.className = "unity-mobile";
    } else {
        canvas.style.width = `${config.width}px`;
        canvas.style.height = `${config.height}px`;
    }

    var buildUrl = `static/web_gl/${config.build_name}/Build`;
    var loaderUrl = buildUrl + `/${config.build_name}.loader.js`;

    var unityConfig = {
        dataUrl: buildUrl + `/${config.build_name}.data`,
        frameworkUrl: buildUrl + `/${config.build_name}.framework.js`,
        codeUrl: buildUrl + `/${config.build_name}.wasm`,
        streamingAssetsUrl: "StreamingAssets",
        companyName: "DefaultCompany",
        productName: config.build_name,
        productVersion: "1.0",
    };
    
    loadingBar.style.display = "block";

    var script = document.createElement("script");
    script.src = loaderUrl;
    script.onload = () => {
        createUnityInstance(canvas, unityConfig, (progress) => {
            progressBarFull.style.width = 100 * progress + "%";
        }).then((instance) => {
            unityInstance = instance; // Store Unity instance globally
            loadingBar.style.display = "none";
            fullscreenButton.onclick = () => {
                unityInstance.SetFullscreen(1);
            };
        }).catch((message) => {
            alert(message);
        });
    };

    document.body.appendChild(script);
}

export function shutdownUnityGame() {
  if (unityInstance) {
      try {
          unityInstance.Quit().then(() => {
              document.getElementById("unity-container")?.remove(); // Remove the Unity canvas container
              unityInstance = null;
              console.log("Unity WebGL instance destroyed.");
          });
      } catch (e) {
          console.warn("Error shutting down Unity instance:", e);
          // Fallback cleanup
          document.getElementById("unity-container")?.remove();
          unityInstance = null;
      }
  }
}


export function terminateUnityScene(data) {
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


function EmitUnityEpisodeResults(json) {
  if (socket && socket.connected) {
      socket.emit('unityEpisodeEnd', JSON.parse(json));
  } else {
      console.warn('Socket.IO is not connected. Cannot emit round results.');
  }
}

function UnityConnectSocketIO() {
  if (socket) {
      console.log('Socket.IO is already connected!');
  } else {
      console.error('Socket.IO connection is not established.');
  }
}