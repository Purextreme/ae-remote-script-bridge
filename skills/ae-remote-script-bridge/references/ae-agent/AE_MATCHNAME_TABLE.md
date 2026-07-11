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

These paths were probed in AE 2024. Reacquire properties after each `addProperty()` call when continuing to edit an indexed group.

| Display | matchName | Notes |
|---|---|---|
| Contents | `ADBE Root Vectors Group` | Shape layer root contents. |
| Group | `ADBE Vector Group` | Add inside root or group contents. |
| Group Contents | `ADBE Vectors Group` | Child contents of a vector group. |
| Group Transform | `ADBE Vector Transform Group` | Transform scoped to a vector group. |
| Rectangle Path | `ADBE Vector Shape - Rect` | Parametric rectangle. |
| Ellipse Path | `ADBE Vector Shape - Ellipse` | Parametric ellipse. |
| Bezier Path | `ADBE Vector Shape - Group` | Freeform shape path. |
| Fill | `ADBE Vector Graphic - Fill` | Vector fill operator. |
| Stroke | `ADBE Vector Graphic - Stroke` | Vector stroke operator. |

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
