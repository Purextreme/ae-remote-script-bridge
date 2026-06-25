(function () {
    app.beginUndoGroup("AE Bridge Create Comp Test");

    try {
        var comp = app.project.items.addComp(
            "AE_Bridge_Create_Comp_Test",
            1920,
            1080,
            1,
            5,
            30
        );

        comp.layers.addSolid(
            [1, 0, 0],
            "AE Bridge Solid",
            1920,
            1080,
            1,
            5
        );

        var textLayer = comp.layers.addText("AE Bridge OK");
        textLayer.property("Position").setValue([960, 540]);

        comp.openInViewer();
    } finally {
        app.endUndoGroup();
    }
})();
