(function () {
    function addPath(contents, name, shape, color, position) {
        var group = contents.addProperty("ADBE Vector Group");
        group.name = name;
        var groupContents = group.property("ADBE Vectors Group");
        var pathGroup = groupContents.addProperty("ADBE Vector Shape - Group");
        pathGroup.property("ADBE Vector Shape").setValue(shape);
        var stroke = groupContents.addProperty("ADBE Vector Graphic - Stroke");
        stroke.property("ADBE Vector Stroke Color").setValue(color);
        stroke.property("ADBE Vector Stroke Width").setValue(18);
        stroke.property("ADBE Vector Stroke Line Cap").setValue(2);
        group.property("ADBE Vector Transform Group")
            .property("ADBE Vector Position")
            .setValue(position);
    }

    function makePolygonArc(radius, segments) {
        var shape = new Shape();
        var vertices = [];
        var tangents = [];
        var i;
        for (i = 0; i <= segments; i += 1) {
            var angle = Math.PI + Math.PI * i / 2 / segments;
            vertices.push([radius * Math.cos(angle), radius * Math.sin(angle)]);
            tangents.push([0, 0]);
        }
        shape.vertices = vertices;
        shape.inTangents = tangents;
        shape.outTangents = tangents;
        shape.closed = false;
        return shape;
    }

    function makeCircularArc(radius, start, end) {
        var delta = end - start;
        var handle = 4 / 3 * Math.tan(Math.abs(delta) / 4) * radius;
        var direction = delta < 0 ? -1 : 1;
        var shape = new Shape();
        shape.vertices = [
            [radius * Math.cos(start), radius * Math.sin(start)],
            [radius * Math.cos(end), radius * Math.sin(end)]
        ];
        shape.inTangents = [
            [0, 0],
            [Math.sin(end) * handle * direction, -Math.cos(end) * handle * direction]
        ];
        shape.outTangents = [
            [-Math.sin(start) * handle * direction, Math.cos(start) * handle * direction],
            [0, 0]
        ];
        shape.closed = false;
        return shape;
    }

    app.beginUndoGroup("AE Smooth Curve Test");
    try {
        var comp = app.project.items.addComp("AE_Smooth_Curve_Test", 1200, 600, 1, 2, 30);
        var layer = comp.layers.addShape();
        layer.name = "Polygon versus Bezier Arc";
        layer.property("ADBE Transform Group")
            .property("ADBE Position")
            .setValue([0, 0]);
        var contents = layer.property("ADBE Root Vectors Group");
        addPath(contents, "Polygon Arc", makePolygonArc(220, 5), [1, 0.2, 0.2], [330, 390]);
        addPath(contents, "Smooth Bezier Arc", makeCircularArc(220, Math.PI, Math.PI * 1.5), [0.15, 0.85, 0.45], [870, 390]);
        comp.openInViewer();
        comp.time = 1;
    } finally {
        app.endUndoGroup();
    }
}());
