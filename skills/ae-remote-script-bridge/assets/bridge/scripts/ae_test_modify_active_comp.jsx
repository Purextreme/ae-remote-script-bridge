(function () {
    app.beginUndoGroup("AE Bridge Modify Active Comp Test");

    try {
        var activeItem = app.project.activeItem;
        if (!(activeItem instanceof CompItem)) {
            throw new Error("Active item is not a composition.");
        }

        activeItem.duration = 8;
        activeItem.bgColor = [0.08, 0.12, 0.18];

        var textLayer = activeItem.layers.addText("Active Comp Modified");
        textLayer.property("Position").setValue([
            activeItem.width / 2,
            activeItem.height / 2
        ]);

        activeItem.openInViewer();
    } finally {
        app.endUndoGroup();
    }
})();
