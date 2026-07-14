# Task: Shape Layers for Icons and UI

Use this card when constructing icons, controls, diagrams, or UI animation with native Shape Layers. Read `../AE_MATCHNAME_TABLE.md` for exact property identifiers.

## Contents

- Construction Workflow
- Hierarchy and Ordering
- Core Patterns
- UI Animation Choices
- Quality and Verification
- Common Failures

## Construction Workflow

1. Identify the object's canonical geometry before copying reference-image perspective or rotation.
2. Build regular geometry with Rectangle, Ellipse, or Polystar paths; use a Bezier `Shape` only for a custom silhouette.
3. Put each distinct icon, control, or independently managed visual element on its own Shape Layer by default. Combine elements only when the user requests it or a shared layer-level transform/operator is intentional.
4. Center each icon part around local `[0, 0]`, then place it with the vector group's Transform.
5. Keep parts of the same element in separate named vector groups when they need independent styling or animation.
6. Add geometry first, then the operators and Fill/Stroke that should act on it.
7. Animate group transforms or focused generator properties instead of rebuilding vertices unnecessarily.

## Hierarchy and Ordering

```text
Shape Layer
└─ Contents (ADBE Root Vectors Group)
   └─ Named Group (ADBE Vector Group)
      ├─ Contents (ADBE Vectors Group)
      │  ├─ Path or parametric generator
      │  ├─ Optional operator
      │  └─ Fill / Stroke
      └─ Transform (ADBE Vector Transform Group)
```

- In the root Contents tested in AE 2024, lower property indexes render in front of higher indexes. Create foreground groups before their background groups, or explicitly verify the final order.
- `addProperty()` on an indexed group can invalidate references to its existing children. Set a newly added child's values before adding the next child, or reacquire it by verified `matchName` or a unique name.
- Keep geometry centered and use Group Transform Position for layout. This separates reusable icon geometry from scene placement.
- Use Layer Transform for whole-icon placement only when all groups should move together.
- Prefer one Shape Layer per distinct element for clearer selection, animation, inspection, and replacement. A single Shape Layer containing many unrelated elements is an explicit optimization or user-directed layout, not the default.

## Core Patterns

Create and place a named group:

```javascript
var root = shapeLayer.property("ADBE Root Vectors Group");
root.addProperty("ADBE Vector Group");
var group = root.property(root.numProperties);
group.name = "Icon Body";
group.property("ADBE Vector Transform Group")
    .property("ADBE Vector Position")
    .setValue([0, 0]);
var contents = group.property("ADBE Vectors Group");
```

Create a rounded rectangle:

```javascript
var rectangle = contents.addProperty("ADBE Vector Shape - Rect");
rectangle.property("ADBE Vector Rect Size").setValue([160, 96]);
rectangle.property("ADBE Vector Rect Position").setValue([0, 0]);
rectangle.property("ADBE Vector Rect Roundness").setValue(32);
```

Create a custom path. Tangents are offsets relative to each vertex, not absolute coordinates:

```javascript
var pathGroup = contents.addProperty("ADBE Vector Shape - Group");
var shape = new Shape();
shape.vertices = [[-40, -50], [-40, 50], [55, 0]];
shape.inTangents = [[0, 0], [0, 0], [0, 0]];
shape.outTangents = [[0, 0], [0, 0], [0, 0]];
shape.closed = true;
pathGroup.property("ADBE Vector Shape").setValue(shape);
```

Create a smooth circular arc with cubic Bezier segments. Keep every segment at or below 90 degrees; the tangent length for a segment with sweep `delta` is `4 / 3 * tan(abs(delta) / 4) * radius`:

```javascript
function makeCircularArc(center, radius, startDegrees, endDegrees) {
    var start = startDegrees * Math.PI / 180;
    var end = endDegrees * Math.PI / 180;
    var sweep = end - start;
    var segmentCount = Math.max(1, Math.ceil(Math.abs(sweep) / (Math.PI / 2)));
    var delta = sweep / segmentCount;
    var vertices = [];
    var inTangents = [];
    var outTangents = [];
    var i;

    for (i = 0; i <= segmentCount; i += 1) {
        var angle = start + delta * i;
        vertices.push([
            center[0] + radius * Math.cos(angle),
            center[1] + radius * Math.sin(angle)
        ]);
        inTangents.push([0, 0]);
        outTangents.push([0, 0]);
    }

    for (i = 0; i < segmentCount; i += 1) {
        var a0 = start + delta * i;
        var a1 = a0 + delta;
        var handle = 4 / 3 * Math.tan(Math.abs(delta) / 4) * radius;
        var direction = delta < 0 ? -1 : 1;
        outTangents[i] = [
            -Math.sin(a0) * handle * direction,
            Math.cos(a0) * handle * direction
        ];
        inTangents[i + 1] = [
            Math.sin(a1) * handle * direction,
            -Math.cos(a1) * handle * direction
        ];
    }

    var shape = new Shape();
    shape.vertices = vertices;
    shape.inTangents = inTangents;
    shape.outTangents = outTangents;
    shape.closed = false;
    return shape;
}
```

- Use an Ellipse Path for a complete circle or ellipse. Do not approximate it with many zero-tangent vertices.
- For a partial circular arc, use the cubic construction above or use an Ellipse Path with Trim Paths when the arc should remain editable or animate its sweep.
- For a non-circular freeform curve, place fewer intentional vertices and calculate non-zero Bezier tangents; adding more zero-tangent vertices only produces a finer polygon.

For organic curves such as faces, hair, eyebrows, and mouths:

- Place anchors at extrema, corners, and intentional changes of curvature rather than at uniform pixel intervals.
- Keep the incoming and outgoing handles collinear at a smooth interior anchor. Change their lengths independently when the curvature differs on each side.
- Use a two-anchor cubic for one clean arch. Do not add a middle anchor unless the curve must change curvature or direction there.
- Aim each endpoint handle along the desired departure direction. Handle direction controls the local slope; handle length controls how long that direction influences the curve.
- Inspect the rendered stroke, not only the path overlay. A thick round-capped stroke can expose flat spots, bulges, and sudden curvature changes that are easy to miss in wireframe view.
- When matching a reference, adjust handles before adding anchors. Add an anchor only when the silhouette cannot be matched without a new curvature event.

Use `assets/bridge/scripts/ae_test_smooth_curves.jsx` to compare a zero-tangent polygon arc with a cubic Bezier arc. Use `assets/bridge/scripts/ae_draw_cartoon_avatar.jsx` as a compact example combining Ellipse paths with freeform face, hair, eyebrow, nose, and mouth curves.

Add style after geometry:

```javascript
var fill = contents.addProperty("ADBE Vector Graphic - Fill");
fill.property("ADBE Vector Fill Color").setValue([0.2, 0.7, 1]);

var stroke = contents.addProperty("ADBE Vector Graphic - Stroke");
stroke.property("ADBE Vector Stroke Color").setValue([1, 1, 1]);
stroke.property("ADBE Vector Stroke Width").setValue(12);
stroke.property("ADBE Vector Stroke Line Cap").setValue(2);
stroke.property("ADBE Vector Stroke Line Join").setValue(2);
```

## UI Animation Choices

- Animate `ADBE Vector Position`, `ADBE Vector Scale`, `ADBE Vector Rotation`, or `ADBE Vector Group Opacity` for independent icon parts.
- Animate Rectangle/Ellipse Position or Size for geometry-driven controls such as toggle knobs and progress tracks.
- Use Trim Paths Start, End, and Offset for line reveals, check draws, rings, and loaders.
- Use Repeater Copies and Repeater Transform for dots, repeated indicators, and radial or linear motifs.
- Use Merge Paths for Boolean-style compound geometry and Round Corners for simple hard-edged paths. Keep each operator in the same vector group as the geometry it should affect, and verify the operator order visually.
- Prefer two or three intentional keys with overshoot over dense keyframes for UI motion. Verify the first, transition, and settled states.

## Quality and Verification

- Build icons upright and symmetric first; apply rotation, scale, and perspective-like placement afterward.
- Prefer parametric roundness for rectangles and round Stroke caps/joins for clean UI edges.
- Avoid tracing compression artifacts or accidental skew from a screenshot into canonical geometry.
- Use `--capture-frame` for incremental checks and `--capture-video` for animated controls. Use `--capture-method render-queue` when an independent final still is useful; do not diagnose a cache defect from one ambiguous capture.
- If foreground geometry appears missing, inspect root group indexes, operator scope, and stale property references first. The current integration tests confirmed an ordering failure but did not reproduce a Shape rendering cache defect.
- Inspect the resulting group names, keyframe counts, and operator paths with a task-specific report; the generic project report does not recurse through Shape contents.

## Common Failures

- Foreground groups hidden behind backgrounds because root group order was assumed rather than verified.
- Stale property references after another `addProperty()` call.
- Absolute tangent coordinates supplied where relative tangent offsets are required.
- Circular arcs approximated with zero-tangent sample points, leaving visible polygon corners.
- Extra middle anchors creating waves or bulges where one cubic arch would be smoother.
- Smooth interior anchors whose incoming and outgoing handles are not collinear.
- Fill or Stroke added outside the vector group containing the intended path.
- One giant Bezier path used where several regular parametric parts would be cleaner and easier to animate.
- Shape construction and scene rotation baked into the same vertices, making later edits fragile.
