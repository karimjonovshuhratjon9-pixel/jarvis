# JARVIS OS V2 — Six-Phase Implementation Notes

This document distinguishes code that exists in this package from features that still require local setup or Windows acceptance testing.

## Phase 1 — Security & Foundation
- Added central tool permission decisions and a local JSONL audit trail under `%USERPROFILE%\.jarvis\audit.jsonl` (or `JARVIS_DATA_DIR`).
- AI-generated Python and unknown planner tools are blocked; there is no fallback to arbitrary code execution.
- Code helper / developer-agent execution and dependency installation are disabled by default. They require `JARVIS_ENABLE_CODE_EXECUTION=1`; this is an opt-in, **not a sandbox**.
- Added rotating logs with API-key redaction and non-invasive startup diagnostics.
- Retained the bounded archive extraction, shell-free app launch and restrictive local CORS changes from the security pass.

## Phase 2 — Intelligence & Memory
- Retained the existing planner, task queue, awareness state, task history and structured long-term memory.
- Added strict plan validation (known tools only, object parameters, maximum eight steps).
- Added an offline SQLite FTS5 memory index with lexical fallback, synchronized from saved long-term facts, plus a `search_memory` tool. It is intentionally described as semantic-style retrieval, not vector embeddings.

## Phase 3 — Voice & Vision
- Retained the existing Gemini Live audio conversation, voice selection / external TTS integration, screen capture and image analysis modules. The assistant prompt now prioritizes Uzbek when the user speaks Uzbek, and the connection loop uses bounded exponential retry backoff.
- The existing UI validates a Gemini key before starting the Live session. The key can be entered after installation; it is not embedded in the archive.
- Camera and screen access remain user-initiated through existing actions; no camera is activated automatically.

## Phase 4 — Autonomous Computer Operator
- Retained existing typed actions for app launch, browser, files, presentations, screen and computer interaction.
- Added centralized permission checks before planner-dispatched tool calls.
- Destructive / external actions are blocked unless the action parameters contain explicit approval. The current UI does not yet provide a universal approval dialog for every tool, so some high-risk actions will fail closed rather than run.
- Generated code is not treated as a safe substitute for typed tools.

## Phase 5 — Proactive AI & Always Active
- Retained the existing Qt system tray and minimize-to-tray behavior.
- Added a tray option and CLI command to register / remove Windows sign-in auto-start for the current user.
- Added an optional local openWakeWord listener. It requires the optional `openwakeword` + `onnxruntime` packages and either a local model file or a supported model name such as `hey_jarvis`. The wake model may be downloaded by the openWakeWord package on first use; audio inference stays on-device, and the Gemini cloud session starts only after detection.
- Wake-word mode is OFF by default. This avoids silently activating the microphone. Set `JARVIS_WAKE_WORD_ENABLED=1` and `JARVIS_WAKE_MODEL` only after installing and selecting a trusted local model.
- Sleep / wake recovery and robust wake-word pause controls still need hands-on Windows validation.

## Phase 6 — QA & Release
- Added focused tests for permissions, plan validation, memory indexing and health checks.
- Added Windows setup / run / PyInstaller helper scripts and a user-facing Uzbek quick-start guide. The UI graphics default is set to Low to reduce load on the target 8 GB RAM laptop.
- The included PyInstaller spec is retained. A packaged EXE must still be built and tested on the target Windows 11 laptop; this Linux build environment cannot certify the Windows installer.

## Known limitations / acceptance gates
- The full UI, audio device, Windows automation, Gemini Live network session, wake-word model, and packaged EXE were not executable in this Linux environment.
- Existing project dependencies include GUI/audio packages that may need Windows-specific installation. Run `python -m pip install -r requirements.txt` in the project `.venv`, then `python -m jarvis --health` or `jarvis --health`.
- Do not enable code execution casually. It runs with the current Windows account permissions and is not isolated.
- Do not place real credentials in a shared ZIP. Add the Gemini key through the app setup screen or a private local `.env` file.
