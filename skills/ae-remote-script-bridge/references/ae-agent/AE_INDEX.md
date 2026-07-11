# AE Agent Reference Index

Use one focused reference instead of loading every file.

| Need | File |
|---|---|
| Normal JSX work, checks, indexes, and common paths | `AE_CORE_RULES.md` |
| Stable property or effect identifier | `AE_MATCHNAME_TABLE.md` |
| Draw icons, controls, or UI animation with Shape Layers | `tasks/shape_layers.md` |
| Import footage or replace a source | `tasks/footage_import_replace.md` |
| Configure or render through Render Queue | `tasks/render_queue.md` |

## Templates

| Template | Use |
|---|---|
| `assets/templates/inspect_active_comp.jsx` | Write active comp summary to this run directory |
| `assets/templates/add_text_layer.jsx` | Add a centered text layer to active comp |
| `assets/templates/add_position_keyframes.jsx` | Add position keyframes to the selected layer |

## Integration Checks

| Script | Use |
|---|---|
| `assets/bridge/scripts/ae_test_shape_ui.jsx` | Build and animate a compact native Shape Layer UI/icon test |

Areas marked `needs_verify` must be probed in AE before use.
