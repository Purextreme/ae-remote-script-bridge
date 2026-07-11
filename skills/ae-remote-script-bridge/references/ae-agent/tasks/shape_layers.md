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
3. Center each icon part around local `[0, 0]`, then place it with the vector group's Transform.
4. Keep independently styled or animated parts in separate named vector groups.
5. Add geometry first, then the operators and Fill/Stroke that should act on it.
6. Animate group transforms or focused generator properties instead of rebuilding vertices unnecessarily.

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
- Fill or Stroke added outside the vector group containing the intended path.
- One giant Bezier path used where several regular parametric parts would be cleaner and easier to animate.
- Shape construction and scene rotation baked into the same vertices, making later edits fragile.
