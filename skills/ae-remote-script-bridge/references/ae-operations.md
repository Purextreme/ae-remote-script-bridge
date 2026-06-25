# AE Operation Patterns

## Inspect Before and After

For destructive or multi-step edits, run `scripts/ae_inspect_project.jsx` before and after the change. Compare `logs/project_structure.json` to confirm the operation changed the intended comp, folder, layer, effect, or keyframe state.

## Create a Task Script

Create a focused JSX script in `scripts/` for the requested operation. Keep it scoped to explicit names or selected/active items. Prefer a task-specific report file when the result cannot be fully captured by `ae_inspect_project.jsx`.

Minimal pattern:

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

## Common Operations

Add an effect:

```javascript
var effects = layer.property("ADBE Effect Parade");
var blur = effects.addProperty("ADBE Gaussian Blur 2");
```

Delete all effects:

```javascript
var effects = layer.property("ADBE Effect Parade");
while (effects.numProperties > 0) {
    effects.property(effects.numProperties).remove();
}
```

Create and delete keyframes:

```javascript
var opacity = layer.property("ADBE Transform Group").property("ADBE Opacity");
opacity.setValueAtTime(0, 0);
opacity.setValueAtTime(1, 100);
while (opacity.numKeys > 0) {
    opacity.removeKey(opacity.numKeys);
}
```

Create a folder and move a comp:

```javascript
var folder = app.project.items.addFolder("Folder Name");
var comp = app.project.items.addComp("Comp Name", 1920, 1080, 1, 5, 30);
comp.parentFolder = folder;
comp.name = "Renamed Comp";
```

Create output, render, and save:

```javascript
var outputFile = new File($.global.AE_BRIDGE_TEMP_DIR + "/render_test.mp4");
var rqItem = app.project.renderQueue.items.add(comp);
rqItem.outputModule(1).file = outputFile;
outputFile = rqItem.outputModule(1).file;
app.project.renderQueue.render();
app.project.save(new File($.global.AE_BRIDGE_TEMP_DIR + "/saved_project.aep"));
```
