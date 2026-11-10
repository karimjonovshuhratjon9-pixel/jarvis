# JARVIS OS V2 — Phase 1 Security Work Report

Status: **IN PROGRESS — core security fixes applied; Phase 1 is not yet complete.**

## Implemented in this working copy

1. `actions/open_app.py`
   - Removed shell-based Windows process launch.
   - Launches resolved binaries with an argument list and `shell=False`.
   - Handles the Windows Settings URI through `os.startfile` rather than `cmd /c start`.
   - Rejects control characters and shell metacharacters in the Start-menu fallback label.
2. `actions/desktop.py`
   - Disabled execution of arbitrary Python returned by the AI model.
   - The previous in-process `exec(compile(...))` sandbox was not a security boundary; generated code now fails closed with a clear message.
   - This temporarily disables the old free-form generated-code desktop action until it is replaced by typed, allowlisted actions in the computer-operator phase.
3. `actions/file_processor.py`
   - Replaced `shutil.unpack_archive` with bounded ZIP/TAR extraction.
   - Rejects traversal and absolute paths, symbolic links, hard links and special TAR entries.
   - Limits archives to 500 entries and 200 MiB extracted data.
4. `api/server.py`
   - Replaced wildcard CORS with an explicit local-origin allowlist configurable through `JARVIS_CORS_ORIGINS`.
   - Disabled credentialed CORS and narrowed methods/headers.
5. `actions/computer_settings.py` and `actions/dev_agent.py`
   - Removed additional `shell=True` calls found during the security sweep.
   - Linux brightness adjustment now uses argument-list subprocess calls.
   - VS Code launch now requires a real executable and uses `shell=False`.
6. Secret hygiene
   - Replaced the exposed-looking value in `.env.example` with a placeholder.
   - Ensured local API-key/credential JSON files are ignored by Git.
   - The deliverable intentionally excludes `.env`, `config/api_keys.json`, `.git`, caches and local runtime data.

## Verification

- `python -m compileall -q .` — passed.
- `python -m pytest tests/test_security.py -q` — **13 passed**.
- `python -m pytest tests/test_security.py tests/test_graphics_capability.py tests/test_api_key_validation.py -q` — **24 passed, 2 subtests passed**.
- Repository-wide scan of Python files for `shell=True`, `shutil.unpack_archive`, and `exec(compile` — no matches.
- `.env.example` checked to contain a placeholder, and local secret files are absent from the deliverable.

## Full-suite limitation

A full `pytest -q` run could not collect all existing tests in this Linux execution environment. Collection errors were caused by missing/runtime-specific dependencies and display support: Google GenAI SDK, PyQt6, sounddevice, and an X11 display required by PyAutoGUI. This does **not** establish that those tests fail on the user's Windows laptop; they remain unverified here.

## Remaining Phase 1 work

- Centralize all API-key reads so modules no longer independently fall back to plaintext `config/api_keys.json`.
- Complete logging rotation, secret redaction and consistent error handling.
- Add startup dependency/health validation and more regression tests.
- Run the complete suite on the target Windows 11 environment and verify existing desktop workflows after replacing generated Python with structured actions.

## Important user action

The uploaded archive contained local credential material. Treat any API key included in that archive as exposed and rotate it in Google AI Studio. Do not put the replacement key into `.env.example` or share it in another ZIP. Add it locally through JARVIS setup or a local `.env` file that is not included in the project archive.
