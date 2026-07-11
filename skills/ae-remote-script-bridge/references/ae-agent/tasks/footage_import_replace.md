# Task: Footage Import / Replace

## Use When

Import files into the project or replace selected AVLayer source.

## Required Checks

- File exists.
- Import uses `new ImportOptions(file)`.
- Replacement target is an `AVLayer`.
- New source is a valid `FootageItem` or `AVItem`.

## Key APIs

- `new File(path)`
- `new ImportOptions(file)`
- `importOptions.canImportAs(type)`
- `app.project.importFile(importOptions)`
- `layer.replaceSource(newSource, fixExpressions)`

## Minimal JSX Pattern

```javascript
var file = new File("C:/path/to/file.png");
if (!file.exists) {
    throw new Error("File does not exist: " + file.fsName);
}

var importOptions = new ImportOptions(file);
var comp = app.project.activeItem;
if (!(comp instanceof CompItem) || comp.selectedLayers.length < 1) {
    throw new Error("Select one layer in a composition.");
}

var layer = comp.selectedLayers[0];
if (!(layer instanceof AVLayer)) {
    throw new Error("The selected layer cannot replace its source.");
}

var footage = null;
app.beginUndoGroup("Import and Replace Source");
try {
    footage = app.project.importFile(importOptions);
    layer.replaceSource(footage, false);
} catch (err) {
    if (footage !== null) {
        footage.remove();
    }
    throw err;
} finally {
    app.endUndoGroup();
}
```

## Common Failures

- Bad Windows path escaping.
- Replacing source on a non-AV layer.
- Using `fixExpressions=true` during bulk replacement.
- Image sequence range options are partly undocumented; mark `needs_verify`.
