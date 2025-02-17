"""
This file provides utilities to inference an ONNX model that has been exported via RLLib. Note that
the structure of the input may change if you've exported with something other than RLLib, so you
may need to reconfigure these if you've done your own export.
"""

from __future__ import annotations

import numpy as np

from interactive_gym.utils import inference_utils

try:
    import onnxruntime as ort
except ImportError:
    raise ImportError(
        "Must `pip install onnxruntime` to use the ONNX inference utils!"
    )


ORT_SESSIONS: dict[str, ort.InferenceSession] = {}


def inference_onnx_model(
    input_dict: dict[str, np.ndarray],
    model_path: str,
) -> np.ndarray:
    """Given an input dict and path to an ONNX model, return the model outputs"""
    # input_dict["seq_lens"] = [
    #     1,
    # ]
    # print(list(input_dict.keys()))
    outputs = ORT_SESSIONS[model_path].run(["output"], input_dict)
    return outputs


def onnx_model_inference_fn(
    observation: dict[str, np.ndarray] | np.ndarray, onnx_model_path: str
):
    # if it's a dictionary observation, the onnx model expects a flattened input array
    if isinstance(observation, dict):
        observation = np.hstack(list(observation.values())).reshape((1, -1))

    # TODO(chase): add compatibility with recurrent networks, must pass state in and seq lens
    model_outputs = inference_onnx_model(
        {
            "obs": observation.astype(np.float32),
            "state_ins": np.array([0.0], dtype=np.float32),  # rllib artifact
        },
        model_path=onnx_model_path,
    )[0].reshape(
        -1
    )  # outputs list of a batch. batch size always 1 so index list and reshape

    action = inference_utils.sample_action_via_softmax(model_outputs)

    return action
    # model_outputs = inference_onnx_model(
    #     {
    #         "obs": observation.astype(np.float32),
    #         # "state_ins": [
    #         #     np.zeros((1, 256), dtype=np.float32) for _ in range(2)
    #         # ],
    #         # "seq_lens": np.array([1], dtype=np.int32),
    #     },
    #     model_path=onnx_model_path,
    # )[0].reshape(
    #     -1
    # )  # outputs list of a batch. batch size always 1 so index list and reshape

    action = inference_utils.sample_action_via_softmax(model_outputs)

    return action


def load_onnx_policy_fn(onnx_model_path: str) -> str:
    """Initialize the ORT session and return the string to access it"""
    if ORT_SESSIONS.get(onnx_model_path) is None:
        ORT_SESSIONS[onnx_model_path] = ort.InferenceSession(
            onnx_model_path, None
        )

    return onnx_model_path
