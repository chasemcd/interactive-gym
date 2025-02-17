export function startUnityScene(data) {
    $("#sceneHeader").show();
    $("#sceneSubHeader").show();
    $("#sceneBody").show();

    // Insert Unity WebGL container and loader elements
    startUnityGame(data, "gameContainer");

    $("#gameContainer").show();


    $("#advanceButton").attr("disabled", false);
    $("#advanceButton").show();

    $("#sceneHeader").html(data.scene_header);
    $("#sceneSubHeader").html(data.scene_subheader);
    $("#sceneBody").html(data.scene_body);
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



function startUnityGame(config, elementId) {
    // Add CSS if it hasn't been added yet
    if (!document.getElementById('unity-custom-styles')) {
        const styleLink = document.createElement('link');
        styleLink.id = 'unity-custom-styles';
        styleLink.rel = 'stylesheet';
        styleLink.type = 'text/css';
        styleLink.href = `static/web_gl/${config.build_name}/TemplateData/style.css`;
        document.head.appendChild(styleLink);
    }

    $(`#${elementId}`).empty()
    
    // Match Unity's exact HTML structure
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
        <div id="unity-build-title">${config.build_name}</div>
      </div>
    </div>`)

    var container = document.querySelector("#unity-container");
    var canvas = document.querySelector("#unity-canvas");
    var loadingBar = document.querySelector("#unity-loading-bar");
    var progressBarFull = document.querySelector("#unity-progress-bar-full");
    var fullscreenButton = document.querySelector("#unity-fullscreen-button");
    var warningBanner = document.querySelector("#unity-warning");

    // Set canvas size through CSS, matching Unity's approach
    if (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) {
        container.className = "unity-mobile";
        canvas.className = "unity-mobile";
    } else {
        // Desktop style
        canvas.style.width = `${config.width}px`;
        canvas.style.height = `${config.height}px`;
    }



    function unityShowBanner(msg, type) {
        function updateBannerVisibility() {
          warningBanner.style.display = warningBanner.children.length ? 'block' : 'none';
        }
        var div = document.createElement('div');
        div.innerHTML = msg;
        warningBanner.appendChild(div);
        if (type == 'error') div.style = 'background: red; padding: 10px;';
        else {
          if (type == 'warning') div.style = 'background: yellow; padding: 10px;';
          setTimeout(function() {
            warningBanner.removeChild(div);
            updateBannerVisibility();
          }, 5000);
        }
        updateBannerVisibility();
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
        showBanner: unityShowBanner,
    };

    loadingBar.style.display = "block";

    var script = document.createElement("script");
    script.src = loaderUrl;
    script.onload = () => {
        createUnityInstance(canvas, unityConfig, (progress) => {
            progressBarFull.style.width = 100 * progress + "%";
        }).then((unityInstance) => {
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