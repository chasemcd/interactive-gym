# Client-Side Usage

This guide covers how to use Interactive Gym in client-side mode, where the environment runs entirely in the browser using Pyodide.

## Overview

Client-side mode runs the environment directly in the user's browser, which has several advantages:

- No server infrastructure required
- Works offline after initial page load
- Lower latency for single-user interactions
- Better privacy as data stays on the user's device

## Prerequisites

- Modern web browser (Chrome, Firefox, Safari, or Edge)
- Stable internet connection (only required for initial page load)
- No additional software installation needed

## Basic Usage

### 1. Create a Simple HTML File

Create an HTML file that loads the Interactive Gym client:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Interactive Gym - Client Side Demo</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/interactive-gym@latest/dist/css/interactive-gym.min.css">
</head>
<body>
    <div id="game-container" style="width: 100%; height: 100vh;"></div>
    
    <script src="https://cdn.jsdelivr.net/pyodide/v0.21.3/full/pyodide.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/interactive-gym@latest/dist/js/interactive-gym.min.js"></script>
    
    <script>
        // Initialize the environment when the page loads
        document.addEventListener('DOMContentLoaded', async () => {
            const gym = await InteractiveGym.init({
                container: '#game-container',
                environment: 'CartPole-v1',  // Default environment
                renderMode: 'human',
                onReady: () => console.log('Environment is ready!'),
                onStep: (obs, reward, done, info) => {
                    console.log('Step completed:', { obs, reward, done, info });
                    if (done) {
                        console.log('Episode finished!');
                    }
                }
            });

            // Example of how to interact with the environment
            window.moveLeft = () => gym.step(0);
            window.moveRight = () => gym.step(1);
            window.resetEnv = () => gym.reset();
        });
    </script>
    
    <div style="position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);">
        <button onclick="moveLeft()">Move Left</button>
        <button onclick="moveRight()">Move Right</button>
        <button onclick="resetEnv()">Reset</button>
    </div>
</body>
</html>
```

### 2. Custom Environments

You can also use custom environments by providing the Python code as a string:

```javascript
const customEnvCode = `
import gymnasium as gym
from gymnasium import spaces
import numpy as np

class CustomEnv(gym.Env):
    def __init__(self):
        self.observation_space = spaces.Box(low=-1, high=1, shape=(4,), dtype=np.float32)
        self.action_space = spaces.Discrete(2)
        self.state = np.zeros(4, dtype=np.float32)
        
    def reset(self, seed=None, options=None):
        self.state = np.random.uniform(-1, 1, size=4).astype(np.float32)
        return self.state, {}
        
    def step(self, action):
        # Simple environment logic
        reward = 1.0 if action == np.argmax(self.state) else -1.0
        self.state = np.roll(self.state, 1)
        done = np.random.random() < 0.05  # 5% chance to end episode
        return self.state, reward, done, False, {}
`;

const gym = await InteractiveGym.init({
    container: '#game-container',
    environment: customEnvCode,  // Pass Python code directly
    renderMode: 'human',
    // ... other options
});
```

## API Reference

### `InteractiveGym.init(options)`

Initialize a new Interactive Gym environment.

**Parameters:**

- `options` (Object): Configuration options
  - `container` (String|HTMLElement): CSS selector or DOM element for the container
  - `environment` (String): Environment name or Python code string
  - `renderMode` (String): Rendering mode ('human', 'rgb_array', 'ansi')
  - `onReady` (Function): Callback when environment is ready
  - `onStep` (Function): Callback after each step
  - `onReset` (Function): Callback when environment is reset
  - `packages` (Array): List of PyPI packages to install
  - `pyodideUrl` (String): Custom Pyodide CDN URL

**Returns:** Promise that resolves to the gym instance

### Instance Methods

#### `gym.step(action)`

Take a step in the environment.

**Parameters:**
- `action`: Action to take (depends on environment)

**Returns:** Promise that resolves to `[observation, reward, done, info]`

#### `gym.reset()`

Reset the environment to its initial state.

**Returns:** Promise that resolves to the initial observation

#### `gym.render(mode)`

Render the current state of the environment.

**Parameters:**
- `mode` (String): Rendering mode ('human', 'rgb_array', 'ansi')

**Returns:** Rendered output (depends on mode)

#### `gym.close()`

Clean up resources used by the environment.

## Advanced Usage

### Loading Pre-trained Models

You can load pre-trained models (in ONNX format) for inference in the browser:

```javascript
const gym = await InteractiveGym.init({
    container: '#game-container',
    environment: 'CartPole-v1',
    onReady: async () => {
        // Load a pre-trained model
        const modelUrl = 'path/to/model.onnx';
        await gym.loadModel(modelUrl);
        
        // Run inference
        const obs = await gym.reset();
        const action = await gym.predict(obs);
        await gym.step(action);
    }
});
```

### Custom Rendering

You can provide a custom rendering function for more control over the display:

```javascript
const gym = await InteractiveGym.init({
    container: '#game-container',
    environment: 'CartPole-v1',
    render: (observation, canvas, info) => {
        // Custom rendering logic here
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Example: Draw a simple representation of the cartpole
        const cartX = (observation[0] + 2.4) / 4.8 * canvas.width;
        const poleAngle = observation[2];
        
        // Draw cart
        ctx.fillStyle = '#3498db';
        ctx.fillRect(cartX - 30, canvas.height - 50, 60, 30);
        
        // Draw pole
        ctx.strokeStyle = '#e74c3c';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(cartX, canvas.height - 50);
        ctx.lineTo(
            cartX + Math.sin(poleAngle) * 100,
            canvas.height - 50 - Math.cos(poleAngle) * 100
        );
        ctx.stroke();
    }
});
```

## Performance Considerations

1. **Bundle Size**: The initial load might be slow due to Pyodide's size (~10MB). Consider:
   - Using a CDN with compression
   - Implementing code splitting
   - Using service workers for offline support

2. **Computation**: Heavy computations can block the main thread. Consider:
   - Using Web Workers for intensive tasks
   - Optimizing your environment code
   - Using WebAssembly for performance-critical parts

3. **Memory**: Large environments or models can consume significant memory. Monitor memory usage and:
   - Dispose of unused resources
   - Use smaller batch sizes for inference
   - Implement garbage collection where needed

## Troubleshooting

### Common Issues

1. **Module Not Found**
   - Ensure all required Python packages are included in the `packages` array
   - Check for case sensitivity in module names

2. **Performance Problems**
   - Reduce the complexity of your environment
   - Use `requestAnimationFrame` for smooth rendering
   - Profile your code to identify bottlenecks

3. **Memory Leaks**
   - Call `close()` when done with environments
   - Avoid creating large objects in loops
   - Monitor memory usage in browser dev tools

### Getting Help

If you encounter issues:
1. Check the browser's developer console for error messages
2. Search the [GitHub issues](https://github.com/chasemcd/interactive-gym/issues)
3. Create a minimal reproducible example
4. Open a new issue with details about your problem

## Examples

### Simple Game Loop

```javascript
async function runEpisode(gym) {
    let obs = await gym.reset();
    let done = false;
    let totalReward = 0;
    
    while (!done) {
        // Simple policy: random actions
        const action = Math.random() < 0.5 ? 0 : 1;
        
        // Take a step
        [obs, reward, done] = await gym.step(action);
        totalReward += reward;
        
        // Render at 60 FPS
        await new Promise(r => requestAnimationFrame(r));
    }
    
    console.log(`Episode finished with total reward: ${totalReward}`);
    return totalReward;
}

// Run multiple episodes
async function runMultipleEpisodes(gym, numEpisodes = 10) {
    const rewards = [];
    for (let i = 0; i < numEpisodes; i++) {
        const reward = await runEpisode(gym);
        rewards.push(reward);
    }
    console.log(`Average reward: ${rewards.reduce((a, b) => a + b, 0) / rewards.length}`);
}
```

### Human-in-the-Loop Training

```javascript
let gym;
let isTraining = false;
let model; // Your machine learning model

async function init() {
    gym = await InteractiveGym.init({
        container: '#game-container',
        environment: 'CartPole-v1',
        onStep: (obs, reward, done) => {
            if (done) {
                console.log('Episode finished!');
                if (isTraining) {
                    setTimeout(() => gym.reset(), 1000);
                }
            }
        }
    });
    
    // Initialize your model here
    // model = await loadModel();
}

// Start/stop training
function toggleTraining() {
    isTraining = !isTraining;
    if (isTraining) {
        trainLoop();
    }
}

async function trainLoop() {
    if (!isTraining) return;
    
    const obs = await gym.getState();
    const action = await model.predict(obs);
    await gym.step(action);
    
    // Continue the loop on the next frame
    requestAnimationFrame(trainLoop);
}

// Human control
window.onkeydown = async (e) => {
    if (!gym) return;
    
    switch(e.key) {
        case 'ArrowLeft':
            await gym.step(0);
            break;
        case 'ArrowRight':
            await gym.step(1);
            break;
        case 'r':
            await gym.reset();
            break;
    }
};

// Initialize when the page loads
window.onload = init;
```

## Browser Support

Interactive Gym client-side mode works in all modern browsers that support:

- WebAssembly
- ES6 Modules
- async/await
- Web Workers (recommended for better performance)

### Recommended Browsers

- Chrome/Edge 80+
- Firefox 74+
- Safari 14.1+
- iOS Safari 14.5+

### Polyfills

For older browsers, you may need to include polyfills for:

- `Promise`
- `fetch`
- `WebAssembly`
- `TextEncoder`/`TextDecoder`

## Security Considerations

When running untrusted code in the browser:

1. **Sandboxing**: All Python code runs in a Web Worker for isolation
2. **Resource Limits**: CPU and memory usage are limited
3. **No File System**: The virtual filesystem is reset on page reload
4. **CORS**: Follows same-origin policy for network requests

## Next Steps

- Learn about [server-side usage](../server_side/) for multi-user scenarios
- Explore [custom environments](../environments/) for your specific needs
- Check out [examples](../examples/) for inspiration
