(function () {
    function setLayerOrigin(layer) {
        layer.property("ADBE Transform Group").property("ADBE Position").setValue([0, 0]);
    }

    function addPathLayer(comp, name, vertices, inTangents, outTangents, closed, fillColor, strokeColor, strokeWidth) {
        var layer = comp.layers.addShape();
        layer.name = name;
        setLayerOrigin(layer);
        var contents = layer.property("ADBE Root Vectors Group");
        var group = contents.addProperty("ADBE Vector Group");
        group.name = name;
        var groupContents = group.property("ADBE Vectors Group");
        var pathGroup = groupContents.addProperty("ADBE Vector Shape - Group");
        var shape = new Shape();
        shape.vertices = vertices;
        shape.inTangents = inTangents;
        shape.outTangents = outTangents;
        shape.closed = closed;
        pathGroup.property("ADBE Vector Shape").setValue(shape);
        if (fillColor) {
            var fill = groupContents.addProperty("ADBE Vector Graphic - Fill");
            fill.property("ADBE Vector Fill Color").setValue(fillColor);
        }
        if (strokeColor && strokeWidth > 0) {
            var stroke = groupContents.addProperty("ADBE Vector Graphic - Stroke");
            stroke.property("ADBE Vector Stroke Color").setValue(strokeColor);
            stroke.property("ADBE Vector Stroke Width").setValue(strokeWidth);
            stroke.property("ADBE Vector Stroke Line Cap").setValue(2);
            stroke.property("ADBE Vector Stroke Line Join").setValue(2);
        }
        return layer;
    }

    function addEllipseLayer(comp, name, size, position, fillColor, strokeColor, strokeWidth) {
        var layer = comp.layers.addShape();
        layer.name = name;
        setLayerOrigin(layer);
        var contents = layer.property("ADBE Root Vectors Group");
        var group = contents.addProperty("ADBE Vector Group");
        group.name = name;
        var groupContents = group.property("ADBE Vectors Group");
        var ellipse = groupContents.addProperty("ADBE Vector Shape - Ellipse");
        ellipse.property("ADBE Vector Ellipse Size").setValue(size);
        ellipse.property("ADBE Vector Ellipse Position").setValue(position);
        var fill = groupContents.addProperty("ADBE Vector Graphic - Fill");
        fill.property("ADBE Vector Fill Color").setValue(fillColor);
        if (strokeColor && strokeWidth > 0) {
            var stroke = groupContents.addProperty("ADBE Vector Graphic - Stroke");
            stroke.property("ADBE Vector Stroke Color").setValue(strokeColor);
            stroke.property("ADBE Vector Stroke Width").setValue(strokeWidth);
        }
        return layer;
    }

    app.beginUndoGroup("Draw Smooth Cartoon Avatar");
    try {
        var comp = app.project.items.addComp("AE_Cartoon_Avatar_Test", 1000, 1000, 1, 3, 30);
        comp.bgColor = [0.08, 0.1, 0.16];
        var outline = [0.12, 0.08, 0.1];
        var skin = [1.0, 0.68, 0.48];
        var hair = [0.12, 0.055, 0.035];

        addEllipseLayer(comp, "Left Ear", [150, 205], [300, 535], skin, outline, 18);
        addEllipseLayer(comp, "Right Ear", [150, 205], [700, 535], skin, outline, 18);

        addPathLayer(comp, "Face",
            [[500, 230], [690, 330], [680, 610], [500, 790], [320, 610], [310, 330]],
            [[-92, -10], [-18, -92], [30, -90], [105, -10], [10, 85], [-38, 88]],
            [[92, -10], [18, 92], [-30, 90], [-105, -10], [-10, -85], [38, -88]],
            true, skin, outline, 22);

        addPathLayer(comp, "Hair Mass",
            [[300, 430], [325, 245], [500, 170], [690, 270], [700, 430], [625, 345], [555, 395], [485, 315], [410, 390]],
            [[-8, 75], [-25, 82], [-95, 8], [-60, -65], [0, -85], [45, 20], [30, -25], [48, 15], [35, -32]],
            [[8, -75], [25, -82], [95, -8], [60, 65], [0, 85], [-45, -20], [-30, 25], [-48, -15], [-35, 32]],
            true, hair, outline, 20);

        addEllipseLayer(comp, "Left Eye White", [126, 88], [405, 500], [1, 0.97, 0.9], outline, 12);
        addEllipseLayer(comp, "Right Eye White", [126, 88], [595, 500], [1, 0.97, 0.9], outline, 12);
        addEllipseLayer(comp, "Left Iris", [48, 58], [418, 505], [0.13, 0.42, 0.48], null, 0);
        addEllipseLayer(comp, "Right Iris", [48, 58], [582, 505], [0.13, 0.42, 0.48], null, 0);
        addEllipseLayer(comp, "Left Pupil", [20, 30], [421, 508], outline, null, 0);
        addEllipseLayer(comp, "Right Pupil", [20, 30], [579, 508], outline, null, 0);
        addEllipseLayer(comp, "Left Eye Highlight", [10, 14], [414, 497], [1, 1, 1], null, 0);
        addEllipseLayer(comp, "Right Eye Highlight", [10, 14], [572, 497], [1, 1, 1], null, 0);

        addPathLayer(comp, "Left Brow",
            [[350, 435], [460, 430]],
            [[0, 0], [-38, -28]],
            [[38, -28], [0, 0]],
            false, null, outline, 18);
        addPathLayer(comp, "Right Brow",
            [[540, 430], [650, 435]],
            [[0, 0], [-38, -28]],
            [[38, -28], [0, 0]],
            false, null, outline, 18);

        addPathLayer(comp, "Nose",
            [[500, 520], [478, 610], [520, 610]],
            [[0, 0], [0, -35], [-20, 0]],
            [[-8, 35], [20, 0], [0, 0]],
            false, null, [0.62, 0.28, 0.22], 10);

        addPathLayer(comp, "Smile",
            [[410, 665], [500, 720], [590, 665]],
            [[0, 0], [-58, 0], [-28, 52]],
            [[28, 52], [58, 0], [0, 0]],
            false, null, [0.48, 0.08, 0.1], 16);

        addEllipseLayer(comp, "Left Cheek", [75, 32], [360, 625], [1, 0.35, 0.36], null, 0)
            .property("ADBE Transform Group").property("ADBE Opacity").setValue(40);
        addEllipseLayer(comp, "Right Cheek", [75, 32], [640, 625], [1, 0.35, 0.36], null, 0)
            .property("ADBE Transform Group").property("ADBE Opacity").setValue(40);

        comp.openInViewer();
        comp.time = 1.5;
    } finally {
        app.endUndoGroup();
    }
}());
