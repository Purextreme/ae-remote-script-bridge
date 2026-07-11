# AE Core Rules

Use this file for normal JSX work. Read a task card for Shape Layer construction, footage replacement, or Render Queue work. Read the matchName table only when a property or effect identifier is needed.

## Always

- Write ExtendScript-compatible JSX: use `var`, plain loops, `File`, and `Folder`.
- Do not use browser APIs, `Promise`, `async`, `fetch`, modern syntax, or expression-only globals in JSX.
- For mutating work, wrap changes in `app.beginUndoGroup()` and `app.endUndoGroup()` with `try/finally`.
- Do not use `--no-protect` for a project edit unless the workflow explicitly permits it.
- Use `$.global.AE_BRIDGE_LOGS_DIR` and `$.global.AE_BRIDGE_TEMP_DIR` for generated files.

## Check Before Use

- Check `app.project.activeItem instanceof CompItem` before comp work.
- Check `comp.selectedLayers.length` before selected-layer work.
- Check `layer.property(...)` results before chaining properties.
- Check `property.canVaryOverTime` before adding keyframes to an unknown property.
- Check `property.canSetExpression` before assigning an expression.

## Index Rules

- Project items, comp layers, properties, and keyframes are usually 1-based.
- `comp.selectedLayers` is a 0-based JavaScript array.
- Remove keyframes from the highest index down.
- Adding a property to an indexed group can invalidate existing property references; reacquire them first.

## Stable Paths

```javascript
var transform = layer.property("ADBE Transform Group");
var position = transform.property("ADBE Position");
var opacity = transform.property("ADBE Opacity");
var sourceText = layer
    .property("ADBE Text Properties")
    .property("ADBE Text Document");
var effects = layer.property("ADBE Effect Parade");
```

- Prefer a verified `matchName` over a display name.
- Editing a `TextDocument` takes effect only after `sourceText.setValue(textDoc)`.
- 2D and 3D Position values have different lengths. Separated Position uses `ADBE Position_0`, `_1`, and `_2`.
- Use `replaceSource(newSource, false)` unless expression fixing is explicitly required.

## Verify In AE

- Render/output templates are localized and user-configurable.
- Shape operators beyond the verified core table, image-sequence range options, AE 26 dropdown fields, and 3D Model Layer APIs are `needs_verify`.
- `app.project.renderQueue.render()` blocks. Treat it as a deliberate final action, not a routine inspection step.
