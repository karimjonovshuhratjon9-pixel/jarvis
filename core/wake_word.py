"""Optional local wake-word listener. It does not stream audio to a cloud service."""
from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Callable


def wait_for_wake_word(on_status: Callable[[str], None] | None = None, stop_event=None) -> bool:
    """Wait for a configured openWakeWord model; return False on setup/runtime failure.

    Install the optional `openwakeword` and `onnxruntime` packages and set
    JARVIS_WAKE_MODEL to a local model path or supported model name such as
    `hey_jarvis`. The audio inference itself remains local.
    """
    model_spec = os.environ.get("JARVIS_WAKE_MODEL", "").strip()
    if not model_spec:
        if on_status: on_status("Wake-word model not configured; cloud voice remains idle.")
        return False
    model_path = Path(model_spec).expanduser()
    if not model_path.is_file() and model_spec.lower() not in {"hey_jarvis", "alexa", "hey_mycroft", "timer", "weather"}:
        if on_status: on_status("Wake-word model path is not a file or a supported openWakeWord model name.")
        return False
    model_source = str(model_path) if model_path.is_file() else model_spec.lower()
    try:
        import numpy as np
        import sounddevice as sd
        from openwakeword.model import Model
        model = Model(wakeword_models=[model_source], inference_framework="onnx")
        threshold = float(os.environ.get("JARVIS_WAKE_THRESHOLD", "0.55"))
        if on_status: on_status("Local wake-word listener active. Say the configured wake phrase.")
        detected = False
        def callback(indata, frames, time_info, status):
            nonlocal detected
            if status:
                return
            audio = (np.asarray(indata[:, 0]) * 32767).astype(np.int16)
            scores = model.predict(audio)
            if scores and max(float(v) for v in scores.values()) >= threshold:
                detected = True
        with sd.InputStream(samplerate=16000, channels=1, dtype="float32", blocksize=1280, callback=callback):
            while not detected and not (stop_event and stop_event.is_set()):
                time.sleep(0.08)
        return detected
    except Exception as exc:
        if on_status: on_status(f"Wake-word listener unavailable: {exc}")
        return False
