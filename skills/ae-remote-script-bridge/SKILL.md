---
name: ae-remote-script-bridge
description: Operate Adobe After Effects from Codex through a Windows AfterFX.com JSX bridge using ExtendScript, not the C++ SDK. Use when the user asks Codex or an agent to inspect, create, modify, organize, render, save, or otherwise automate an open After Effects project with code; when JSX scripts must be sent to AE from the command line; when AE version compatibility, match names, or app.project state must be verified from inside After Effects.
---

# AE Remote Script Bridge

## Core Workflow

Use this skill on Windows with Adobe After Effects. Prefer the bridge project already present in the current workspace when it contains `client/send_to_ae.py` and `config.json`.

If the current workspace does not contain a bridge, copy `assets/bridge/` from this skill into the workspace first, preserving its directory structure. Then edit `config.json` only if `AfterFX.com` is installed somewhere other than:

```text
C:\Program Files\Adobe\Adobe After Effects 2024\Support Files\AfterFX.com
```

Do not use `AfterFX.exe -r`; this bridge intentionally uses `AfterFX.com -r`.

## Documentation Policy

This project uses After Effects ExtendScript, not the C++ SDK. Use ExtendScript-compatible JavaScript.

For simple, common operations already covered by this skill or local examples, write JSX directly. For complex operations, version-sensitive APIs, unfamiliar property paths, effect match names, render/output-module behavior, text/font APIs, 3D/model APIs, or after repeated AE errors, look up the current scripting reference before writing or retrying code:

- Primary reference: `https://ae-scripting.docsforadobe.dev/`
- Official Adobe scripts reference: `https://helpx.adobe.com/after-effects/using/scripts.html`
- Adobe After Effects developer entry point: `https://developer.adobe.com/after-effects/`

Before using APIs added in recent AE releases, inspect the running AE version from inside AE and compare it with the scripting guide changelog. Prefer graceful fallback or report the version mismatch instead of assuming availability.

## Running JSX

Run JSX through:

```bat
py -3.12 client\send_to_ae.py scripts\your_script.jsx
```

Use `python` instead of `py -3.12` only when that is the available Python launcher. The bridge:

- reads `config.json`
- generates `temp/ae_bridge_wrapper.jsx`
- injects `AE_BRIDGE_ROOT`, `AE_BRIDGE_LOGS_DIR`, `AE_BRIDGE_TEMP_DIR`, and `AE_BRIDGE_RESULT_PATH` into ExtendScript globals
- calls `subprocess.run([afterfx_com_path, "-r", wrapper_path])`
- waits for `logs/latest_result.json`

Treat `[AE OK]` as proof that the JSX finished without throwing, not as proof that the AE project changed as intended.

## Verifying AE State

After any meaningful AE operation, verify state from inside AE. Use:

```bat
py -3.12 client\send_to_ae.py scripts\ae_inspect_project.jsx
```

Then read `logs/project_structure.json` and compare it to the requested outcome. Verify concrete facts such as comp name, dimensions, duration, layer names, layer text, parent folder, effect counts, keyframe counts, render output file, and saved project path.

For custom operations, write a small JSX script into `scripts/`, run it through the bridge, then run `ae_inspect_project.jsx` or write a task-specific report JSON into `logs/`.

For version-sensitive tasks, first run or write a tiny probe script that reports at least `app.version`, `app.buildName`, `app.buildNumber`, `app.isoLanguage`, and any needed availability checks such as `typeof app.fonts`, `app.effects`, or `propertyGroup.canAddProperty(matchName)`.

## JSX Authoring Rules

Use ExtendScript-compatible JavaScript:

- prefer `var`
- avoid modern JS syntax
- use `app.beginUndoGroup()` and `app.endUndoGroup()` for project edits
- use `$.writeln()` or file logging for debug output
- write reports as JSON manually when needed
- avoid `alert()` in normal success paths
- prefer explicit AE match names for effects and properties, for example `ADBE Effect Parade`, `ADBE Gaussian Blur 2`, `ADBE Glo2`, `ADBE Transform Group`, `ADBE Opacity`
- use `canAddProperty()` before `addProperty()` when adding masks, effects, text animators, or other properties whose match name is uncertain
- remember that adding to indexed groups can invalidate existing property references; store `propertyIndex` and reacquire properties from the parent group when adding multiple effects/properties
- do not assume project attributes are writable; confirm read/write status in the scripting guide or by a small probe before assignment

When writing files from JSX, use the injected globals:

```javascript
var logsDir = $.global.AE_BRIDGE_LOGS_DIR;
var tempDir = $.global.AE_BRIDGE_TEMP_DIR;
```

## Built-In Checks

Use these scripts to confirm the bridge still works:

```bat
py -3.12 client\send_to_ae.py scripts\ae_test_create_comp.jsx
py -3.12 client\send_to_ae.py scripts\ae_test_modify_active_comp.jsx
py -3.12 client\send_to_ae.py scripts\ae_test_error.jsx
py -3.12 client\send_to_ae.py scripts\ae_test_integration_ops.jsx
py -3.12 client\send_to_ae.py scripts\ae_inspect_project.jsx
```

`ae_test_integration_ops.jsx` validates adding/deleting effects, creating/deleting keyframes, creating folders, moving and renaming a comp, creating an output, rendering, and saving a project.

## Reference

Read `references/ae-operations.md` when the task needs examples for custom JSX operations or validation patterns.
