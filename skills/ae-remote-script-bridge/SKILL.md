---
name: ae-remote-script-bridge
description: Operate Adobe After Effects from Codex through a Windows AfterFX.com JSX bridge. Use when the user asks Codex or an agent to inspect, create, modify, organize, render, save, or otherwise automate an open After Effects project with code; when JSX scripts must be sent to AE 2024 from the command line; or when AE project state must be verified by reading app.project rather than trusting command success alone.
---

# AE Remote Script Bridge

## Core Workflow

Use this skill on Windows with Adobe After Effects 2024. Prefer the bridge project already present in the current workspace when it contains `client/send_to_ae.py` and `config.json`.

If the current workspace does not contain a bridge, copy `assets/bridge/` from this skill into the workspace first, preserving its directory structure. Then edit `config.json` only if `AfterFX.com` is installed somewhere other than:

```text
C:\Program Files\Adobe\Adobe After Effects 2024\Support Files\AfterFX.com
```

Do not use `AfterFX.exe -r`; this bridge intentionally uses `AfterFX.com -r`.

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

## JSX Authoring Rules

Use ExtendScript-compatible JavaScript:

- prefer `var`
- avoid modern JS syntax
- use `app.beginUndoGroup()` and `app.endUndoGroup()` for project edits
- write reports as JSON manually when needed
- avoid `alert()` in normal success paths
- prefer explicit AE match names for effects and properties, for example `ADBE Effect Parade`, `ADBE Gaussian Blur 2`, `ADBE Transform Group`, `ADBE Opacity`

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
