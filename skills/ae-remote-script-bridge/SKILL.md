---
name: ae-remote-script-bridge
description: Operate Adobe After Effects from Codex through a Windows AfterFX.com JSX bridge and a lightweight AE scripting reference. Use when Codex needs to inspect, create, modify, organize, render, save, or verify an open After Effects project with ExtendScript/JSX; when an agent needs AE scripting rules, common APIs, match names, pitfalls, task cards, or runnable JSX templates; or when AE version compatibility, match names, or app.project state must be checked from inside After Effects.
---

# AE Remote Script Bridge

Use this skill for After Effects scripting with ExtendScript JSX, not the C++ SDK and not browser JavaScript.

## Reference Workflow

This `SKILL.md` is the single workflow guide. For APIs, match names, pitfalls, or task-specific examples, start with `references/ae-agent/AE_INDEX.md`.

Read only the needed reference file:

- Frequent scripting APIs: `references/ae-agent/AE_API_TABLE.md`
- Common match names: `references/ae-agent/AE_MATCHNAME_TABLE.md`
- Common failure modes: `references/ae-agent/AE_PITFALLS.md`
- Task-specific cards: `references/ae-agent/tasks/`

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

By default, `send_to_ae.py` protects the user's project before running a target script:

- AE must have an open project.
- The project must already be saved to an `.aep` file.
- The project must not have unsaved changes.
- The bridge copies the current `.aep` into an `agent backups/` folder next to the project file with an `agent backup` prefix and keeps the latest 10 backups.

If the project is unsaved or dirty, the bridge writes an `[AE ERROR]` result for the agent and shows an AE alert for the user before the target JSX runs. Use `--no-protect` only for read-only checks, disposable bridge tests, or explicitly approved recovery workflows.

For multi-command agent work, generate one stable `--operation-id` for the user request and pass it to every mutating bridge call in that request. The first call performs the saved/clean check and creates the backup; later calls with the same `--operation-id` reuse that backup and do not block on dirty state created by earlier calls. Use a new `--operation-id` for the next user request.

The bridge injects these ExtendScript globals:

```javascript
$.global.AE_BRIDGE_ROOT
$.global.AE_BRIDGE_LOGS_DIR
$.global.AE_BRIDGE_TEMP_DIR
$.global.AE_BRIDGE_RESULT_PATH
```

Use them for reports and temporary outputs instead of hardcoded paths.

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

The Render Queue method isolates the capture item, temporarily disables existing queued items, restores them, and removes the capture item after rendering.

## Verification Workflow

After any meaningful AE operation, run:

```bat
python client\send_to_ae.py --no-protect scripts\ae_inspect_project.jsx
```

Then read `logs/project_structure.json` and compare concrete facts: comp names, dimensions, duration, layer names, text, source names, effect counts, keyframe counts, output files, and saved project paths.

When visual appearance matters, also capture a frame after the operation or batch. Do not capture after every tiny change. Prefer `--capture-time-mode middle` or `--capture-time-mode two-thirds` for animated comps unless the user's request points to a specific time. Use the default `saveframe-8bpc` capture for routine checks; use `--capture-method render-queue` only when color fidelity needs confirmation.

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

Write After Effects scripts as ExtendScript-compatible `.jsx`:

- Prefer `var`.
- Do not use `let`, `const`, arrow functions, classes, template literals, destructuring, `Promise`, `async`, `await`, `fetch`, `XMLHttpRequest`, browser DOM APIs, `window`, or `document`.
- Use plain `for` loops; avoid relying on modern Array methods.
- Use ExtendScript `File` and `Folder` for filesystem work.

Project safety:

- Run mutating scripts through the bridge's default protection.
- Reuse one `--operation-id` across all bridge calls in the same user request.
- Use `--no-protect` only for read-only checks, disposable bridge tests, or explicitly approved recovery workflows.
- Wrap project edits with `app.beginUndoGroup("name")` and `app.endUndoGroup()`.
- Use `try/finally` so `endUndoGroup()` runs after failures.
- Before active comp work, check `app.project.activeItem instanceof CompItem`.
- Before selected-layer work, check `comp.selectedLayers.length`.
- Remember AE collection indexes are often 1-based: `app.project.item(1)`, `comp.layer(1)`, `property.keyTime(1)`.
- Remember `comp.selectedLayers` is a 0-based JavaScript array.

Property access:

- Prefer stable `matchName` values where known, for example `ADBE Transform Group`, `ADBE Position`, `ADBE Opacity`, `ADBE Effect Parade`.
- Do not invent match names. If a matchName is not verified, mark it `needs_verify`.
- Display names can be localized; use them only when no verified matchName is known or when the API requires a template/display string.
- Always null-check property lookups before using returned objects.
- Adding properties to indexed groups can invalidate existing references. Reacquire properties after `addProperty()` when continuing work.

Text:

- `Source Text` is a `TextDocument` property.
- Read it with `.value`, edit the `TextDocument`, then write it back with `.setValue(textDoc)`.

Output and expressions:

- Avoid `alert()` in normal workflows.
- Prefer `$.writeln()` or writing a small report file.
- With this bridge, prefer `$.global.AE_BRIDGE_LOGS_DIR` for reports.
- After key visual edits or a long batch of changes, use `--capture-frame` so the agent can inspect a rendered PNG. Avoid capture for routine read-only checks because AE may mark the project dirty after temporary bit-depth changes. Use `--capture-method render-queue` only when the default preview has obvious color issues or needs high-fidelity confirmation.
- Scripting API and expression runtime are separate. `property.expression = "..."` assigns an expression string; it does not mean expression APIs are available to JSX.
- Check `property.canSetExpression` before setting expressions.

## Built-In Bridge Checks

Use these from the bridge root:

```bat
python client\send_to_ae.py --no-protect scripts\ae_test_create_comp.jsx
python client\send_to_ae.py --no-protect scripts\ae_test_modify_active_comp.jsx
python client\send_to_ae.py --no-protect scripts\ae_test_error.jsx
python client\send_to_ae.py --no-protect scripts\ae_test_integration_ops.jsx
python client\send_to_ae.py --no-protect scripts\ae_inspect_project.jsx
```
