---
name: ae-remote-script-bridge
description: Operate Adobe After Effects from Codex through a Windows AfterFX.com JSX bridge and a lightweight AE scripting reference. Use when Codex needs to inspect, create, modify, organize, render, save, or verify an open After Effects project with ExtendScript/JSX; when an agent needs AE scripting rules, common APIs, match names, pitfalls, task cards, or runnable JSX templates; or when AE version compatibility, match names, or app.project state must be checked from inside After Effects.
---

# AE Remote Script Bridge

Use this skill for After Effects scripting with ExtendScript JSX, not the C++ SDK and not browser JavaScript.

## Reference Workflow

This `SKILL.md` owns bridge workflow. For JSX rules, match names, or high-risk tasks, choose one focused file from `references/ae-agent/AE_INDEX.md`.

Use bundled templates from `assets/templates/` when they fit the task:

- `inspect_active_comp.jsx`
- `add_text_layer.jsx`
- `add_position_keyframes.jsx`

Do not load long external docs unless the local reference marks an area `needs_verify`, the API is version-sensitive, or AE returns repeated errors.

## Bridge Setup

Prefer an existing workspace bridge when it contains:

```text
client/send_to_ae.py
scripts/
logs/
temp/
```

If the workspace does not contain a bridge, copy `assets/bridge/` from this skill into the workspace. The copied bridge is self-contained.

The bridge uses `AfterFX.com -r`, not `AfterFX.exe -r`.

`client/send_to_ae.py` resolves `AfterFX.com` in this order:

1. `--afterfx "C:\path\to\AfterFX.com"`
2. `AFTERFX_COM_PATH`
3. optional bridge-local `config.json` with `afterfx_com_path`
4. automatic search under `C:\Program Files\Adobe\Adobe After Effects *\Support Files\AfterFX.com`

If automatic discovery fails, create a bridge-local `config.json` based on `config.example.json` or pass `--afterfx`.

## Running JSX

From the bridge root:

```bat
python client\send_to_ae.py scripts\your_script.jsx
```

or with an explicit AE path:

```bat
python client\send_to_ae.py --afterfx "C:\path\to\AfterFX.com" scripts\your_script.jsx
```

Use `--timeout-seconds <seconds>` when a deliberate long-running operation needs more than the default 60-second limit. A timeout stops the client wait but cannot guarantee that AE stopped an already-running JSX. After a timeout, treat project state as unknown; wait for AE to respond and run a read-only inspection before any further mutation.

By default, `send_to_ae.py` protects the user's project before running a target script:

- AE must have an open project.
- The project must already be saved to an `.aep` file.
- The project must not have unsaved changes.
- The bridge copies the current `.aep` into an `agent backups/` folder next to the project file with an `agent backup` prefix and keeps the latest 10 backups.

If the project is unsaved or dirty, the bridge writes an `[AE ERROR]` result for the agent and shows an AE alert for the user before the target JSX runs. Use `--no-protect` only for read-only checks, disposable bridge tests, or explicitly approved recovery workflows.

For multi-command agent work, generate one stable `--operation-id` for the user request and pass it to every mutating bridge call in that request. The first call performs the saved/clean check and creates the backup; later calls with the same `--operation-id` reuse that backup and do not block on dirty state created by earlier calls. Protection state expires after 24 hours. Use a new `--operation-id` for the next user request.

The bridge injects these ExtendScript globals:

```javascript
$.global.AE_BRIDGE_ROOT
$.global.AE_BRIDGE_LOGS_DIR
$.global.AE_BRIDGE_TEMP_DIR
$.global.AE_BRIDGE_RESULT_PATH
```

Use them for reports and temporary outputs instead of hardcoded paths.

Every command prints a `Run ID` and `Run Dir`. The run directory contains `result.json`, any task-specific reports, wrapper JSX, and optional visual previews. The bridge keeps the latest 10 run directories.

Treat `[AE OK]` as proof that JSX finished without throwing. For meaningful changes, verify AE state from inside AE.

For key visual operations or after a batch of changes, request a frame capture in the same command:

```bat
python client\send_to_ae.py scripts\your_script.jsx --capture-frame --capture-time-mode two-thirds
```

Use `--capture-time-mode current`, `middle`, `two-thirds`, or `end`, or pass `--capture-time <seconds>`. For animated comps, choose a middle or middle-late frame when it better represents the result. By default, the bridge captures a preview by temporarily switching the project to `8 bpc`, calling `saveFrameToPng`, and restoring the original bit depth. This avoids touching the user's Render Queue and is usually sufficient for agent visual checks. The bridge writes a resized preview PNG with a long edge of at most 1500 px. AE may still mark the project dirty because the project bit depth was touched; the capture report includes `dirtyChangedByCapture` and the client prints a warning when this happens.

If colors look suspicious, or if the project depends on HDR, linear workflow, or 32-bit highlights, verify with the Render Queue capture path:

```bat
python client\send_to_ae.py scripts\your_script.jsx --capture-frame --capture-method render-queue --capture-time-mode two-thirds
```

The Render Queue method isolates the capture item, temporarily disables existing queued items, restores them, restores the comp time, and removes the capture item after rendering. Render and output template names depend on the local AE installation; treat a missing `Best Settings` or `PNG` template as a local configuration failure.

For animated comps or after a batch of timing-sensitive changes, request a low-frame-rate preview video instead of relying only on a still frame:

```bat
python client\send_to_ae.py scripts\your_script.jsx --capture-video
```

Use this only when animation, transitions, temporal effects, or multiple sequential edits need visual verification. The preview video path temporarily switches the project to `8 bpc`, captures a capped PNG sequence with `saveFrameToPng`, restores the original bit depth, then writes the MP4 and contact sheet under the current run's `temp/video_preview/` directory. It does not use or modify Render Queue. Defaults are 4 fps playback, at most 48 sampled frames, and a 960 px maximum edge. Treat this as an agent inspection preview, not a final color-fidelity render.

## Reference Images and Shape Construction

Prioritize geometric quality over literal reproduction when recreating shapes from screenshots, video, or web images. A reference can contain incidental perspective, tilt, scaling artifacts, or capture distortion. For inherently regular objects such as icons, mouse cursors, symmetric marks, and rectangular controls, first build a clean, canonical, front-facing shape with correct proportions and curves. Then separately apply rotation, scale, position, or other scene-fitting transforms. If a one-step recreation would reduce quality, split construction from placement; when the intended angle or distortion is ambiguous, ask the user rather than baking accidental reference-image skew into the asset.

For programmatic Shape Layer construction, read `references/ae-agent/tasks/shape_layers.md` and the verified paths in `references/ae-agent/AE_MATCHNAME_TABLE.md`. Probe operators not listed there before using them.

## Verification Workflow

After any meaningful AE operation, run:

```bat
python client\send_to_ae.py --no-protect scripts\ae_inspect_project.jsx
```

Then read `<Run Dir>/project_structure.json` and compare its concrete facts: project path, active item, comp names and dimensions, layer names and timing, text, source names, effect counts, and opacity keyframe counts. Use a task-specific report for other properties, keyframes, Render Queue state, and output files.

When visual appearance matters, also capture a frame after the operation or batch. Do not capture after every tiny change. Prefer `--capture-time-mode middle` or `--capture-time-mode two-thirds` for animated comps unless the user's request points to a specific time. Use the default `saveframe-8bpc` capture for routine checks; use `--capture-method render-queue` only when color fidelity needs confirmation. If the comp has meaningful animation or the task changed timing across several moments, use `--capture-video` once at the end so the agent can inspect both the generated MP4 and contact sheet.

For version-sensitive work, write a tiny probe script that reports `app.version`, `app.buildName`, `app.buildNumber`, `app.isoLanguage`, and feature availability checks:

```javascript
(function () {
    var logsDir = $.global.AE_BRIDGE_LOGS_DIR;
    var reportFile = new File(logsDir + "/ae_version_probe.json");

    reportFile.encoding = "UTF-8";
    reportFile.open("w");
    reportFile.write("{");
    reportFile.write('"version":"' + app.version + '"');
    reportFile.write(',"buildName":"' + app.buildName + '"');
    reportFile.write(',"buildNumber":' + app.buildNumber);
    reportFile.write(',"isoLanguage":"' + app.isoLanguage + '"');
    reportFile.write(',"hasFontsObject":' + (typeof app.fonts !== "undefined" ? "true" : "false"));
    reportFile.write("}");
    reportFile.close();
})();
```

Prefer a task-specific report file when the result cannot be fully captured by `ae_inspect_project.jsx`:

```javascript
(function () {
    var logsDir = $.global.AE_BRIDGE_LOGS_DIR;
    var reportFile = new File(logsDir + "/task_result.json");

    app.beginUndoGroup("Task Name");
    try {
        var comp = app.project.activeItem;
        if (!(comp instanceof CompItem)) {
            throw new Error("Active item is not a composition.");
        }

        // Make the AE changes here.

        reportFile.encoding = "UTF-8";
        reportFile.open("w");
        reportFile.write('{"ok":true}');
        reportFile.close();
    } finally {
        app.endUndoGroup();
    }
})();
```

## JSX Authoring Rules

Read `references/ae-agent/AE_CORE_RULES.md` before writing normal JSX. For every mutating request, reuse one `--operation-id` across the related bridge calls. Use `--no-protect` only for read-only checks, disposable tests, or explicitly approved recovery work.

Write reports to `$.global.AE_BRIDGE_LOGS_DIR` and temporary outputs to `$.global.AE_BRIDGE_TEMP_DIR`. Avoid `alert()` in normal workflows. Use the frame or video capture options only after meaningful visual changes.

## Built-In Bridge Checks

Use these from the bridge root:

```bat
python -m unittest discover -s client -p test_send_to_ae.py
python client\send_to_ae.py --no-protect scripts\ae_test_create_comp.jsx
python client\send_to_ae.py --no-protect scripts\ae_test_modify_active_comp.jsx
python client\send_to_ae.py --no-protect scripts\ae_test_error.jsx
python client\send_to_ae.py --no-protect scripts\ae_test_integration_ops.jsx
python client\send_to_ae.py --no-protect scripts\ae_test_shape_ui.jsx --capture-frame --capture-method render-queue --capture-time 1
python client\send_to_ae.py --no-protect scripts\ae_inspect_project.jsx
```
