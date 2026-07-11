(function () {
    var logsDir = $.global.AE_BRIDGE_LOGS_DIR;
    var reportFile = new File(logsDir + "/shape_ui_test.json");
    var compName = "AE_Shape_UI_Test";
    var backgroundSourceName = "AE_Shape_UI_Test_Background";
    var comp = null;

    function removeOldComp() {
        var i;
        for (i = app.project.numItems; i >= 1; i -= 1) {
            var item = app.project.item(i);
            if (item instanceof CompItem && item.name === compName) {
                item.remove();
            }
        }
        for (i = app.project.numItems; i >= 1; i -= 1) {
            var source = app.project.item(i);
            if (source instanceof FootageItem && source.name === backgroundSourceName) {
                source.remove();
            }
        }
    }

    function createGroup(layer, name, position) {
        var root = layer.property("ADBE Root Vectors Group");
        root.addProperty("ADBE Vector Group");
        var group = root.property(root.numProperties);
        group.name = name;
        group.property("ADBE Vector Transform Group")
            .property("ADBE Vector Position")
            .setValue(position);
        return group;
    }

    function groupContents(group) {
        return group.property("ADBE Vectors Group");
    }

    function addRectangle(group, size, position, roundness) {
        var rectangle = groupContents(group).addProperty("ADBE Vector Shape - Rect");
        rectangle.property("ADBE Vector Rect Size").setValue(size);
        rectangle.property("ADBE Vector Rect Position").setValue(position || [0, 0]);
        rectangle.property("ADBE Vector Rect Roundness").setValue(roundness || 0);
    }

    function addEllipse(group, size, position) {
        var ellipse = groupContents(group).addProperty("ADBE Vector Shape - Ellipse");
        ellipse.property("ADBE Vector Ellipse Size").setValue(size);
        ellipse.property("ADBE Vector Ellipse Position").setValue(position || [0, 0]);
    }

    function addPath(group, vertices, inTangents, outTangents, closed) {
        var pathGroup = groupContents(group).addProperty("ADBE Vector Shape - Group");
        var shape = new Shape();
        shape.vertices = vertices;
        shape.inTangents = inTangents;
        shape.outTangents = outTangents;
        shape.closed = closed;
        pathGroup.property("ADBE Vector Shape").setValue(shape);
    }

    function zeroTangents(count) {
        var tangents = [];
        var i;
        for (i = 0; i < count; i += 1) {
            tangents.push([0, 0]);
        }
        return tangents;
    }

    function addFill(group, color, opacity) {
        var fill = groupContents(group).addProperty("ADBE Vector Graphic - Fill");
        fill.property("ADBE Vector Fill Color").setValue(color);
        fill.property("ADBE Vector Fill Opacity").setValue(opacity === undefined ? 100 : opacity);
    }

    function addStroke(group, color, width, round) {
        var stroke = groupContents(group).addProperty("ADBE Vector Graphic - Stroke");
        stroke.property("ADBE Vector Stroke Color").setValue(color);
        stroke.property("ADBE Vector Stroke Width").setValue(width);
        if (round) {
            stroke.property("ADBE Vector Stroke Line Cap").setValue(2);
            stroke.property("ADBE Vector Stroke Line Join").setValue(2);
        }
    }

    function animateScale(group, times, values) {
        var scale = group.property("ADBE Vector Transform Group")
            .property("ADBE Vector Scale");
        var i;
        for (i = 0; i < times.length; i += 1) {
            scale.setValueAtTime(times[i], values[i]);
        }
    }

    function buildCursor(layer) {
        var group = createGroup(layer, "Cursor Icon", [-455, -165]);
        var vertices = [
            [-46, -68], [-46, 67], [-12, 35], [12, 82],
            [37, 69], [13, 24], [62, 21]
        ];
        addPath(group, vertices, zeroTangents(vertices.length), zeroTangents(vertices.length), true);
        addFill(group, [0.95, 0.97, 1]);
        addStroke(group, [0.08, 0.11, 0.18], 8, true);
        var position = group.property("ADBE Vector Transform Group")
            .property("ADBE Vector Position");
        position.setValueAtTime(0, [-500, -205]);
        position.setValueAtTime(0.45, [-445, -155]);
        position.setValueAtTime(0.65, [-455, -165]);
    }

    function buildCheck(layer) {
        var check = createGroup(layer, "Check Mark", [-275, -165]);
        var vertices = [[-39, 2], [-10, 32], [45, -35]];
        addPath(check, vertices, zeroTangents(3), zeroTangents(3), false);
        addStroke(check, [1, 1, 1], 17, true);
        animateScale(check, [0, 0.32, 0.5], [[0, 0], [118, 118], [100, 100]]);

        var background = createGroup(layer, "Check Background", [-275, -165]);
        addRectangle(background, [145, 145], [0, 0], 34);
        addFill(background, [0.12, 0.68, 0.48]);
    }

    function buildPlay(layer) {
        var play = createGroup(layer, "Play Triangle", [-82, -165]);
        var vertices = [[-30, -43], [-30, 43], [47, 0]];
        addPath(play, vertices, zeroTangents(3), zeroTangents(3), true);
        addFill(play, [1, 1, 1]);

        var background = createGroup(layer, "Play Background", [-90, -165]);
        addEllipse(background, [145, 145], [0, 0]);
        addFill(background, [0.22, 0.46, 0.95]);
    }

    function buildMergedPlus(layer) {
        var group = createGroup(layer, "Merged Plus", [105, -165]);
        addRectangle(group, [38, 125], [0, 0], 0);
        addRectangle(group, [125, 38], [0, 0], 0);
        groupContents(group).addProperty("ADBE Vector Filter - Merge");
        var roundCorners = groupContents(group).addProperty("ADBE Vector Filter - RC");
        roundCorners.property("ADBE Vector RoundCorner Radius").setValue(13);
        addFill(group, [0.95, 0.38, 0.28]);
        animateScale(group, [0, 0.4, 0.62], [[70, 70], [112, 112], [100, 100]]);
    }

    function buildToggle(layer) {
        var knob = createGroup(layer, "Toggle Knob", [330, -165]);
        addEllipse(knob, [82, 82], [-52, 0]);
        addFill(knob, [0.2, 0.72, 1]);
        var knobPosition = groupContents(knob)
            .property("ADBE Vector Shape - Ellipse")
            .property("ADBE Vector Ellipse Position");
        knobPosition.setValueAtTime(0, [-52, 0]);
        knobPosition.setValueAtTime(0.55, [58, 0]);
        knobPosition.setValueAtTime(0.72, [52, 0]);

        var track = createGroup(layer, "Toggle Track", [330, -165]);
        addRectangle(track, [210, 104], [0, 0], 52);
        addFill(track, [0.15, 0.19, 0.27]);
    }

    function buildLoader(layer) {
        var group = createGroup(layer, "Loading Ring", [-390, 155]);
        addEllipse(group, [145, 145], [0, 0]);
        addStroke(group, [0.68, 0.36, 1], 17, true);
        var trim = groupContents(group).addProperty("ADBE Vector Filter - Trim");
        trim.property("ADBE Vector Trim Start").setValue(8);
        var end = trim.property("ADBE Vector Trim End");
        var offset = trim.property("ADBE Vector Trim Offset");
        end.setValueAtTime(0, 25);
        end.setValueAtTime(1, 82);
        end.setValueAtTime(2, 25);
        offset.setValueAtTime(0, 0);
        offset.setValueAtTime(2, 720);
    }

    function buildRepeaterDots(layer) {
        var group = createGroup(layer, "Repeater Dots", [-130, 155]);
        addEllipse(group, [34, 34], [-38, 0]);
        addFill(group, [0.18, 0.82, 0.76]);
        var repeater = groupContents(group).addProperty("ADBE Vector Filter - Repeater");
        repeater.property("ADBE Vector Repeater Copies").setValue(3);
        repeater.property("ADBE Vector Repeater Transform")
            .property("ADBE Vector Repeater Position")
            .setValue([38, 0]);
        var opacity = group.property("ADBE Vector Transform Group")
            .property("ADBE Vector Group Opacity");
        opacity.setValueAtTime(0, 35);
        opacity.setValueAtTime(0.5, 100);
        opacity.setValueAtTime(1, 35);
    }

    function buildStar(layer) {
        var group = createGroup(layer, "Polystar", [90, 155]);
        var star = groupContents(group).addProperty("ADBE Vector Shape - Star");
        star.property("ADBE Vector Star Type").setValue(1);
        star.property("ADBE Vector Star Points").setValue(5);
        star.property("ADBE Vector Star Inner Radius").setValue(36);
        star.property("ADBE Vector Star Outer Radius").setValue(76);
        star.property("ADBE Vector Star Outer Roundess").setValue(8);
        addFill(group, [1, 0.76, 0.18]);
        var rotation = group.property("ADBE Vector Transform Group")
            .property("ADBE Vector Rotation");
        rotation.setValueAtTime(0, 0);
        rotation.setValueAtTime(2, 144);
    }

    app.beginUndoGroup("AE Shape UI Integration Test");
    try {
        removeOldComp();
        comp = app.project.items.addComp(compName, 1200, 700, 1, 3, 30);
        comp.bgColor = [0.035, 0.05, 0.08];

        var background = comp.layers.addSolid(
            [0.035, 0.05, 0.08],
            backgroundSourceName,
            comp.width,
            comp.height,
            1,
            comp.duration
        );
        background.name = "UI Background";
        background.moveToEnd();

        var shapeLayer = comp.layers.addShape();
        shapeLayer.name = "UI Icon System";
        buildCursor(shapeLayer);
        buildCheck(shapeLayer);
        buildPlay(shapeLayer);
        buildMergedPlus(shapeLayer);
        buildToggle(shapeLayer);
        buildLoader(shapeLayer);
        buildRepeaterDots(shapeLayer);
        buildStar(shapeLayer);

        comp.openInViewer();
        comp.time = 1;

        var root = shapeLayer.property("ADBE Root Vectors Group");
        if (root.numProperties !== 11) {
            throw new Error("Expected 11 shape groups, found " + root.numProperties + ".");
        }
        var checkScaleKeys = root.property("Check Mark")
            .property("ADBE Vector Transform Group")
            .property("ADBE Vector Scale").numKeys;
        var toggleKeys = root.property("Toggle Knob")
            .property("ADBE Vectors Group")
            .property("ADBE Vector Shape - Ellipse")
            .property("ADBE Vector Ellipse Position").numKeys;
        var trimKeys = root.property("Loading Ring")
            .property("ADBE Vectors Group")
            .property("ADBE Vector Filter - Trim")
            .property("ADBE Vector Trim Offset").numKeys;
        if (checkScaleKeys !== 3 || toggleKeys !== 3 || trimKeys !== 2) {
            throw new Error("Shape animation keyframe counts did not match expectations.");
        }
        reportFile.encoding = "UTF-8";
        reportFile.open("w");
        reportFile.write("{");
        reportFile.write('"ok":true');
        reportFile.write(',"compName":"' + comp.name + '"');
        reportFile.write(',"shapeLayer":"' + shapeLayer.name + '"');
        reportFile.write(',"groupCount":' + root.numProperties);
        reportFile.write(',"checkScaleKeys":' + checkScaleKeys);
        reportFile.write(',"togglePositionKeys":' + toggleKeys);
        reportFile.write(',"trimOffsetKeys":' + trimKeys);
        reportFile.write(',"duration":' + comp.duration);
        reportFile.write(',"width":' + comp.width);
        reportFile.write(',"height":' + comp.height);
        reportFile.write("}");
        reportFile.close();
    } finally {
        app.endUndoGroup();
    }
})();
