import * as ort from 'https://cdnjs.cloudflare.com/ajax/libs/onnxruntime-web/1.10.0/ort.min.js';

// Store loaded models to avoid reloading
const loadedModels = {};
const hiddenStates = {};

export async function actionFromONNX(policyID, observation) {
    // Conduct forward inference
    const logits = await inferenceONNXPolicy(policyID, observation);

    // Apply softmax to convert logits to probabilities
    const probabilities = softmax(logits);

    // Sample an action based on the probabilities
    const action = sampleAction(probabilities);

    return action;
}

async function inferenceONNXPolicy(policyID, observation) {
    
    // Load the model if not already loaded
    if (!loadedModels[policyID]) {
        loadedModels[policyID] = await window.ort.InferenceSession.create(
            policyID, {executionProviders: ["webgl"],}
          );
    }
    
    const session = loadedModels[policyID];
    
    // Prepare input tensor(s) from the observation
    const inputTensor = new window.ort.Tensor('float32', observation, [observation.length]);

    const feeds = {};
    feeds[session.inputNames[0]] = inputTensor;

    // Run inference
    const results = await session.run(feeds);

    // Get the output logits (assuming single output)
    const logits = results[session.outputNames[0]].data;

    return logits
}

// Softmax function to convert logits to probabilities
function softmax(logits) {
    const maxLogit = Math.max(...logits);
    const exps = logits.map(logit => Math.exp(logit - maxLogit));
    const sumExps = exps.reduce((a, b) => a + b, 0);
    return exps.map(exp => exp / sumExps);
}

// Function to sample an action based on probabilities
function sampleAction(probabilities) {
    const cumulativeProbabilities = probabilities.reduce((acc, prob) => {
        if (acc.length === 0) {
            return [prob];
        } else {
            return [...acc, acc[acc.length - 1] + prob];
        }
    }, []);

    const randomValue = Math.random();

    for (let i = 0; i < cumulativeProbabilities.length; i++) {
        if (randomValue < cumulativeProbabilities[i]) {
            return i;
        }
    }

    // Fallback in case of floating-point precision issues
    return cumulativeProbabilities.length - 1;
}