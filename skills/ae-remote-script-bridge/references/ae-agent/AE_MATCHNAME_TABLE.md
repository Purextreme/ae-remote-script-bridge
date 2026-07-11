# AE MatchName Table

Only common verified match names are included. Do not guess missing values.

## Layer Top Level

| Display | matchName | Notes |
|---|---|---|
| AV Layer | `ADBE AV Layer` | AVLayer root. |
| Marker | `ADBE Marker` | Top-level layer marker group/property. |
| Time Remap | `ADBE Time Remapping` | Requires time remap enabled. |
| Masks | `ADBE Mask Parade` | Mask group. |
| Effects | `ADBE Effect Parade` | Effect group. |
| Essential Properties | `ADBE Layer Overrides` | Version-sensitive workflows. |

## Transform

| Display | matchName | Notes |
|---|---|---|
| Transform | `ADBE Transform Group` | Transform group. |
| Anchor Point | `ADBE Anchor Point` | 2D or 3D value. |
| Position | `ADBE Position` | 2D or 3D value. |
| X Position | `ADBE Position_0` | Separated dimension. |
| Y Position | `ADBE Position_1` | Separated dimension. |
| Z Position | `ADBE Position_2` | Separated dimension, 3D. |
| Scale | `ADBE Scale` | Percentage array. |
| Orientation | `ADBE Orientation` | 3D layers. |
| X Rotation | `ADBE Rotate X` | 3D layers. |
| Y Rotation | `ADBE Rotate Y` | 3D layers. |
| Z Rotation | `ADBE Rotate Z` | Common 2D rotation path too. |
| Opacity | `ADBE Opacity` | 0..100. |

## Text

| Display | matchName | Notes |
|---|---|---|
| Text Layer | `ADBE Text Layer` | Text layer root. |
| Text | `ADBE Text Properties` | Text group. |
| Source Text | `ADBE Text Document` | `TextDocument` property. |
| Path Options | `ADBE Text Path Options` | Text-on-path controls. |
| Animators | `ADBE Text Animators` | Text animator group. |
| Animator | `ADBE Text Animator` | Added inside Animators. |
| Range Selector | `ADBE Text Selector` | Text selector. |
| Animator Properties | `ADBE Text Animator Properties` | Animator property group. |
| Text Position | `ADBE Text Position 3D` | Text animator property. |
| Text Opacity | `ADBE Text Opacity` | Text animator property. |
| Text Fill Color | `ADBE Text Fill Color` | Text animator property. |

## Audio

| Display | matchName | Notes |
|---|---|---|
| Audio | `ADBE Audio Group` | Audio group. |
| Audio Levels | `ADBE Audio Levels` | Audio levels property. |

## Shape Layer Core

These paths were probed in AE 2024. Reacquire child properties after each `addProperty()` call on an indexed group.

### Containers and Transform

| Display | matchName | Notes |
|---|---|---|
| Shape Layer | `ADBE Vector Layer` | Shape layer root. |
| Contents | `ADBE Root Vectors Group` | Shape layer root contents. |
| Group | `ADBE Vector Group` | Add inside root or group contents. |
| Group Contents | `ADBE Vectors Group` | Child contents of a vector group. |
| Group Transform | `ADBE Vector Transform Group` | Transform scoped to a vector group. |
| Group Position | `ADBE Vector Position` | Local group position. |
| Group Scale | `ADBE Vector Scale` | Local group scale. |
| Group Rotation | `ADBE Vector Rotation` | Local group rotation. |
| Group Opacity | `ADBE Vector Group Opacity` | Local group opacity. |

### Generators and Paths

| Display | matchName | Notes |
|---|---|---|
| Rectangle Path | `ADBE Vector Shape - Rect` | Parametric rectangle. |
| Rectangle Size | `ADBE Vector Rect Size` | `[width, height]`. |
| Rectangle Position | `ADBE Vector Rect Position` | Local generator position. |
| Rectangle Roundness | `ADBE Vector Rect Roundness` | Corner radius. |
| Ellipse Path | `ADBE Vector Shape - Ellipse` | Parametric ellipse. |
| Ellipse Size | `ADBE Vector Ellipse Size` | `[width, height]`. |
| Ellipse Position | `ADBE Vector Ellipse Position` | Local generator position. |
| Polystar Path | `ADBE Vector Shape - Star` | Star or polygon generator. |
| Polystar Type | `ADBE Vector Star Type` | Star/polygon selector. |
| Polystar Points | `ADBE Vector Star Points` | Point count. |
| Inner Radius | `ADBE Vector Star Inner Radius` | Star inner radius. |
| Outer Radius | `ADBE Vector Star Outer Radius` | Star/polygon outer radius. |
| Bezier Path Group | `ADBE Vector Shape - Group` | Freeform path container. |
| Bezier Path | `ADBE Vector Shape` | `Shape` value with relative tangents. |

### Style and Operators

| Display | matchName | Notes |
|---|---|---|
| Fill | `ADBE Vector Graphic - Fill` | Add in the same group as its geometry. |
| Fill Color | `ADBE Vector Fill Color` | RGB array, values 0..1. |
| Fill Opacity | `ADBE Vector Fill Opacity` | 0..100. |
| Stroke | `ADBE Vector Graphic - Stroke` | Add in the same group as its geometry. |
| Stroke Color | `ADBE Vector Stroke Color` | RGB array, values 0..1. |
| Stroke Opacity | `ADBE Vector Stroke Opacity` | 0..100. |
| Stroke Width | `ADBE Vector Stroke Width` | Pixel width. |
| Stroke Line Cap | `ADBE Vector Stroke Line Cap` | Value `2` produced round caps in AE 2024. |
| Stroke Line Join | `ADBE Vector Stroke Line Join` | Value `2` produced round joins in AE 2024. |
| Trim Paths | `ADBE Vector Filter - Trim` | Line reveal and loader operator. |
| Trim Start | `ADBE Vector Trim Start` | Percentage. |
| Trim End | `ADBE Vector Trim End` | Percentage. |
| Trim Offset | `ADBE Vector Trim Offset` | Degrees. |
| Repeater | `ADBE Vector Filter - Repeater` | Repeated geometry operator. |
| Repeater Copies | `ADBE Vector Repeater Copies` | Copy count. |
| Repeater Offset | `ADBE Vector Repeater Offset` | Source-copy offset. |
| Repeater Transform | `ADBE Vector Repeater Transform` | Repeater-local transform group. |
| Repeater Position | `ADBE Vector Repeater Position` | Per-copy position delta. |
| Round Corners | `ADBE Vector Filter - RC` | Rounds compatible paths. |
| Round Corners Radius | `ADBE Vector RoundCorner Radius` | Radius in pixels. |
| Merge Paths | `ADBE Vector Filter - Merge` | Boolean-style path combination. |
| Merge Mode | `ADBE Vector Merge Type` | Probe desired mode visually before relying on non-default values. |

## Common Effects

| Display | matchName | Notes |
|---|---|---|
| Gaussian Blur | `ADBE Gaussian Blur 2` | Current common Gaussian Blur. |
| Gaussian Blur (Legacy) | `ADBE Gaussian Blur` | Legacy; avoid unless needed. |
| Glow | `ADBE Glo2` | Common Glow effect. |
| Fill | `ADBE Fill` | Generate effect. |
| Tint | `ADBE Tint` | Color correction effect. |
| Slider Control | `ADBE Slider Control` | Expression Controls category. |

## Needs Verify / Avoid Guessing

| Area | Status | Notes |
|---|---|---|
| Shape operators beyond the core table | `needs_verify` | Probe repeaters, trim paths, merge paths, and other operators before use. |
| Render/output module template names | `needs_verify` | Names depend on AE version/language/user templates. |
| Import image sequence range options | `needs_verify` | Some range fields are undocumented in source docs. |
| New AE 26 dropdown menu property fields | `needs_verify` | Version-sensitive. Probe `app.version` first. |
| 3D Model Layer APIs | `needs_verify` | New and sparse. Avoid in generic templates. |
