import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from capture_preview import (
    DEFAULT_CAPTURE_MAX_EDGE,
    DEFAULT_VIDEO_CAPTURE_FPS,
    DEFAULT_VIDEO_CAPTURE_MAX_EDGE,
    DEFAULT_VIDEO_CAPTURE_MAX_FRAMES,
    build_render_queue_capture_jsx,
    build_saveframe_8bpc_capture_jsx,
    build_saveframe_8bpc_sequence_capture_jsx,
    normalize_capture,
    normalize_video_capture,
)
from run_context import MAX_RUNS, create_run_context, prune_run_contexts


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
PROTECTION_STATE_PATH = PROJECT_ROOT / "logs" / "protection_state.json"
TIMEOUT_SECONDS = 60
DEFAULT_ADOBE_DIR = Path("C:/Program Files/Adobe")
BACKUP_PREFIX = "agent backup"
BACKUP_DIR_NAME = "agent backups"
MAX_BACKUPS = 10
PROTECTION_STATE_MAX_AGE = dt.timedelta(hours=24)


def fail(message):
    print(message, file=sys.stderr)
    return 1


def to_extendscript_path(path):
    return str(path.resolve()).replace("\\", "/")


def escape_extendscript_string(value):
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


def json_bool(value):
    return "true" if value else "false"


def write_text_file(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_config_afterfx_path():
    if not CONFIG_PATH.exists():
        return None
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    afterfx_com_path = config.get("afterfx_com_path")
    if afterfx_com_path:
        return Path(afterfx_com_path)
    if config:
        raise ValueError("config.json must contain afterfx_com_path.")
    return None


def afterfx_version_key(path):
    app_dir = path.parent.parent.name
    parts = [int(part) for part in re.findall(r"\d+", app_dir)]
    return parts if parts else [0]


def find_afterfx_com():
    if not DEFAULT_ADOBE_DIR.exists():
        return None

    candidates = []
    for app_dir in DEFAULT_ADOBE_DIR.glob("Adobe After Effects *"):
        candidate = app_dir / "Support Files" / "AfterFX.com"
        if candidate.exists():
            candidates.append(candidate)

    if not candidates:
        return None

    candidates.sort(key=afterfx_version_key, reverse=True)
    return candidates[0]


def resolve_afterfx_path(cli_afterfx_path):
    if cli_afterfx_path:
        path = Path(cli_afterfx_path)
        if not path.exists():
            raise FileNotFoundError("--afterfx path not found: " + str(path))
        return path

    env_afterfx_path = os.environ.get("AFTERFX_COM_PATH")
    if env_afterfx_path:
        path = Path(env_afterfx_path)
        if not path.exists():
            raise FileNotFoundError(
                "AFTERFX_COM_PATH path not found: " + str(path)
            )
        return path

    config_afterfx_path = load_config_afterfx_path()
    if config_afterfx_path:
        if not config_afterfx_path.exists():
            raise FileNotFoundError(
                "config.json afterfx_com_path not found: "
                + str(config_afterfx_path)
            )
        return config_afterfx_path

    discovered_path = find_afterfx_com()
    if discovered_path:
        return discovered_path

    raise FileNotFoundError(
        "AfterFX.com not found. Provide one of:\n"
        + "1. --afterfx \"C:\\path\\to\\AfterFX.com\"\n"
        + "2. AFTERFX_COM_PATH environment variable\n"
        + "3. config.json with afterfx_com_path next to this bridge"
    )


def build_wrapper_jsx(target_jsx, run_context):
    target_path = escape_extendscript_string(to_extendscript_path(target_jsx))
    bridge_root = escape_extendscript_string(to_extendscript_path(PROJECT_ROOT))
    logs_dir = escape_extendscript_string(to_extendscript_path(run_context.run_dir))
    temp_dir = escape_extendscript_string(to_extendscript_path(run_context.temp_dir))
    result_path = escape_extendscript_string(
        to_extendscript_path(run_context.result_path)
    )
    run_id = escape_extendscript_string(run_context.run_id)

    return """(function () {
    var targetFile = new File("%s");
    var resultFile = new File("%s");
    var runId = "%s";
    $.global.AE_BRIDGE_ROOT = "%s";
    $.global.AE_BRIDGE_LOGS_DIR = "%s";
    $.global.AE_BRIDGE_TEMP_DIR = "%s";
    $.global.AE_BRIDGE_RESULT_PATH = "%s";

    function escapeJson(value) {
        var text = String(value);
        text = text.replace(/\\\\/g, "\\\\\\\\");
        text = text.replace(/"/g, '\\\\"');
        text = text.replace(/\\r/g, "\\\\r");
        text = text.replace(/\\n/g, "\\\\n");
        text = text.replace(/\\t/g, "\\\\t");
        return text;
    }

    function writeResult(ok, message, line) {
        resultFile.encoding = "UTF-8";
        resultFile.open("w");
        resultFile.write("{");
        resultFile.write('"ok":' + (ok ? "true" : "false"));
        resultFile.write(',"runId":"' + runId + '"');
        resultFile.write(',"message":"' + escapeJson(message) + '"');
        if (line !== null && line !== undefined) {
            resultFile.write(',"line":' + line);
        }
        resultFile.write("}");
        resultFile.close();
    }

    try {
        $.evalFile(targetFile);
        writeResult(true, "Script executed successfully.", null);
    } catch (err) {
        writeResult(false, err.toString(), err.line);
    }
})();""" % (
        target_path,
        result_path,
        run_id,
        bridge_root,
        logs_dir,
        temp_dir,
        result_path,
    )


def build_preflight_jsx(show_alert, allow_dirty, result_path):
    result_path = escape_extendscript_string(to_extendscript_path(result_path))

    return """(function () {
    var resultFile = new File("%s");
    var showAlert = %s;
    var allowDirty = %s;

    function escapeJson(value) {
        var text = String(value);
        text = text.replace(/\\\\/g, "\\\\\\\\");
        text = text.replace(/"/g, '\\\\"');
        text = text.replace(/\\r/g, "\\\\r");
        text = text.replace(/\\n/g, "\\\\n");
        text = text.replace(/\\t/g, "\\\\t");
        return text;
    }

    function quoted(value) {
        return '"' + escapeJson(value) + '"';
    }

    function writeResult(ok, message, projectFile, dirty) {
        resultFile.encoding = "UTF-8";
        resultFile.open("w");
        resultFile.write("{");
        resultFile.write('"ok":' + (ok ? "true" : "false"));
        resultFile.write(',"message":' + quoted(message));
        resultFile.write(',"projectFile":' + quoted(projectFile || ""));
        resultFile.write(',"dirty":' + (dirty ? "true" : "false"));
        resultFile.write("}");
        resultFile.close();
    }

    var message = "";
    var projectFile = "";
    var dirty = false;

    try {
        if (!app.project) {
            message = "AE Bridge safety guard: no open After Effects project was found.";
        } else {
            dirty = !!app.project.dirty;
            if (!app.project.file) {
                message = "AE Bridge safety guard: the current project has not been saved yet. Save the project before allowing agent operations so a backup can be created.";
            } else if (dirty && !allowDirty) {
                message = "AE Bridge safety guard: the current project has unsaved changes. Save the project before allowing agent operations so the backup matches the current state.";
                projectFile = app.project.file.fsName;
            } else {
                projectFile = app.project.file.fsName;
            }
        }

        if (message !== "") {
            writeResult(false, message, projectFile, dirty);
            if (showAlert) {
                alert(message);
            }
            return;
        }

        writeResult(true, "Project is saved and clean.", projectFile, false);
    } catch (err) {
        writeResult(false, err.toString(), projectFile, dirty);
        if (showAlert) {
            alert(err.toString());
        }
    }
})();""" % (
        result_path,
        json_bool(show_alert),
        json_bool(allow_dirty),
    )


def wait_for_result(result_path, deadline, expected_run_id=None):
    last_json_error = None
    mismatched_run_id = None
    while time.monotonic() < deadline:
        if result_path.exists():
            try:
                with result_path.open("r", encoding="utf-8-sig") as result_file:
                    result = json.load(result_file)
                if expected_run_id and result.get("runId") != expected_run_id:
                    mismatched_run_id = result.get("runId")
                else:
                    return result
            except json.JSONDecodeError as err:
                last_json_error = err
        time.sleep(0.2)
    if last_json_error is not None:
        raise RuntimeError("Result JSON remained incomplete: " + str(last_json_error))
    if mismatched_run_id is not None:
        raise RuntimeError(
            "Result runId did not match. Expected "
            + expected_run_id
            + ", received "
            + str(mismatched_run_id)
        )
    raise RuntimeError("No result JSON was generated.")


def run_afterfx_script(
    afterfx_com_path,
    jsx_path,
    result_path,
    stage,
    timeout_seconds=TIMEOUT_SECONDS,
    expected_run_id=None,
):
    if result_path.exists():
        result_path.unlink()

    started_at = time.monotonic()
    deadline = started_at + timeout_seconds
    command = [str(afterfx_com_path), "-r", str(jsx_path)]

    try:
        completed = subprocess.run(
            command,
            timeout=max(0.1, deadline - time.monotonic()),
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired as err:
        raise RuntimeError(
            "AfterFX.com timed out during "
            + stage
            + " after "
            + str(timeout_seconds)
            + " seconds. JSX: "
            + str(jsx_path)
            + "\nAfter Effects may still be executing the JSX. Treat project state as unknown and run a read-only inspection before any further mutation."
        ) from err

    try:
        result = wait_for_result(result_path, deadline, expected_run_id)
    except (OSError, RuntimeError) as err:
        detail = completed.stderr.strip()
        message = "Could not read result for " + stage + ": " + str(err)
        message += "\nAfterFX.com exit code: " + str(completed.returncode)
        if detail:
            message += "\nAfterFX.com stderr: " + detail
        raise RuntimeError(message) from err

    result["bridge"] = {
        "stage": stage,
        "durationMs": round((time.monotonic() - started_at) * 1000),
        "afterfxExitCode": completed.returncode,
    }
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def make_backup(project_file):
    source = Path(project_file)
    if not source.exists():
        raise FileNotFoundError("Project file not found for backup: " + str(source))

    backup_dir = source.parent / BACKUP_DIR_NAME
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    safe_stem = re.sub(r"[^A-Za-z0-9_. -]+", "_", source.stem).strip() or "project"
    backup_path = (
        backup_dir
        / (BACKUP_PREFIX + " " + safe_stem + " " + timestamp + source.suffix)
    )
    shutil.copy2(source, backup_path)
    backup_path.touch()

    backups = sorted(
        backup_dir.glob(BACKUP_PREFIX + " *.aep"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for stale_backup in backups[MAX_BACKUPS:]:
        stale_backup.unlink()

    return backup_path


def load_protection_state():
    if not PROTECTION_STATE_PATH.exists():
        return {}
    try:
        with PROTECTION_STATE_PATH.open("r", encoding="utf-8-sig") as state_file:
            state = json.load(state_file)
    except (OSError, json.JSONDecodeError):
        return {}

    now = dt.datetime.now()
    active_state = {}
    for operation_id, operation_state in state.items():
        try:
            created_at = dt.datetime.fromisoformat(operation_state["createdAt"])
        except (KeyError, TypeError, ValueError):
            continue
        if now - created_at <= PROTECTION_STATE_MAX_AGE:
            active_state[operation_id] = operation_state

    if active_state != state:
        save_protection_state(active_state)
    return active_state


def save_protection_state(state):
    PROTECTION_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROTECTION_STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_operation_state(operation_id):
    if not operation_id:
        return None
    return load_protection_state().get(operation_id)


def set_operation_state(operation_id, project_file, backup_path):
    if not operation_id:
        return
    state = load_protection_state()
    state[operation_id] = {
        "projectFile": str(project_file),
        "backupPath": str(backup_path),
        "createdAt": dt.datetime.now().isoformat(timespec="seconds"),
    }
    save_protection_state(state)


def print_stage_diagnostics(result):
    bridge = result.get("bridge", {})
    if not bridge:
        return
    print("AfterFX.com Exit Code: " + str(bridge.get("afterfxExitCode", "")))
    print("Stage Duration: " + str(bridge.get("durationMs", "")) + " ms")


def main():
    parser = argparse.ArgumentParser(
        description="Send a JSX file to Adobe After Effects through AfterFX.com."
    )
    parser.add_argument("script", help="Path to the .jsx script to run.")
    parser.add_argument(
        "--afterfx",
        help="Optional explicit path to AfterFX.com. Overrides env/config/search.",
    )
    parser.add_argument(
        "--no-protect",
        action="store_true",
        help="Skip saved/clean project guard and backup. Use only for read-only checks or disposable tests.",
    )
    parser.add_argument(
        "--no-alert",
        action="store_true",
        help="Do not show AE alert dialogs for protection failures.",
    )
    parser.add_argument(
        "--operation-id",
        help="Stable id for one agent operation. The first call backs up the project; later calls with the same id reuse that protection.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=TIMEOUT_SECONDS,
        help="Maximum time for each AfterFX.com execution, including result collection.",
    )
    parser.add_argument(
        "--capture-frame",
        action="store_true",
        help="After the script finishes, capture the active comp frame for visual inspection.",
    )
    parser.add_argument(
        "--capture-method",
        choices=["saveframe-8bpc", "render-queue"],
        default="saveframe-8bpc",
        help="Frame capture method. Default is a fast 8-bpc saveFrameToPng preview; use render-queue for color-fidelity checks.",
    )
    parser.add_argument(
        "--capture-time-mode",
        choices=["current", "middle", "two-thirds", "end"],
        default="current",
        help="Frame time to capture when --capture-frame is used and --capture-time is omitted.",
    )
    parser.add_argument(
        "--capture-time",
        type=float,
        help="Exact comp time in seconds to capture when --capture-frame is used.",
    )
    parser.add_argument(
        "--capture-max-edge",
        type=int,
        default=DEFAULT_CAPTURE_MAX_EDGE,
        help="Resize captured preview so its long edge is at most this size. Use 0 to keep original size.",
    )
    parser.add_argument(
        "--capture-video",
        action="store_true",
        help="After the script finishes, capture a low-frame-rate preview video of the active comp for animation inspection.",
    )
    parser.add_argument(
        "--capture-video-fps",
        type=float,
        default=DEFAULT_VIDEO_CAPTURE_FPS,
        help="Sample and playback fps for --capture-video. Long comps are capped by --capture-video-max-frames.",
    )
    parser.add_argument(
        "--capture-video-max-frames",
        type=int,
        default=DEFAULT_VIDEO_CAPTURE_MAX_FRAMES,
        help="Maximum number of frames to sample for --capture-video. Use 0 to disable the cap.",
    )
    parser.add_argument(
        "--capture-video-max-edge",
        type=int,
        default=DEFAULT_VIDEO_CAPTURE_MAX_EDGE,
        help="Resize video preview frames so their long edge is at most this size. Use 0 to keep original size.",
    )
    args = parser.parse_args()

    if args.timeout_seconds <= 0:
        return fail("[INPUT ERROR]\n--timeout-seconds must be greater than 0.")
    if args.capture_video_fps <= 0:
        return fail("[INPUT ERROR]\n--capture-video-fps must be greater than 0.")
    if args.capture_video_max_frames < 0:
        return fail("[INPUT ERROR]\n--capture-video-max-frames cannot be negative.")
    if args.capture_max_edge < 0:
        return fail("[INPUT ERROR]\n--capture-max-edge cannot be negative.")
    if args.capture_video_max_edge < 0:
        return fail("[INPUT ERROR]\n--capture-video-max-edge cannot be negative.")

    try:
        afterfx_com_path = resolve_afterfx_path(args.afterfx)
    except (OSError, ValueError, json.JSONDecodeError) as err:
        return fail("[CONFIG ERROR]\n" + str(err))

    jsx_path = Path(args.script)
    if not jsx_path.is_absolute():
        jsx_path = (Path.cwd() / jsx_path).resolve()
    else:
        jsx_path = jsx_path.resolve()

    if not jsx_path.exists():
        return fail("[INPUT ERROR]\nJSX file not found: " + str(jsx_path))

    if jsx_path.suffix.lower() != ".jsx":
        return fail("[INPUT ERROR]\nExpected a .jsx file: " + str(jsx_path))

    prune_run_contexts(PROJECT_ROOT, MAX_RUNS - 1)
    run_context = create_run_context(PROJECT_ROOT)

    print("Run ID: " + run_context.run_id)
    print("Run Dir: " + str(run_context.run_dir))

    if not args.no_protect:
        operation_state = get_operation_state(args.operation_id)
        if operation_state and Path(operation_state.get("backupPath", "")).exists():
            write_text_file(
                run_context.preflight_jsx_path,
                build_preflight_jsx(
                    False,
                    True,
                    run_context.preflight_result_path,
                ),
            )
            try:
                preflight_result = run_afterfx_script(
                    afterfx_com_path,
                    run_context.preflight_jsx_path,
                    run_context.preflight_result_path,
                    "preflight",
                    args.timeout_seconds,
                )
            except RuntimeError as err:
                return fail("[AE ERROR]\n" + str(err))

            if not preflight_result.get("ok"):
                print("[AE ERROR]")
                print(preflight_result.get("message", "Project protection check failed."))
                return 1

            if preflight_result.get("projectFile") != operation_state.get("projectFile"):
                print("[AE ERROR]")
                print(
                    "Operation protection state belongs to a different project: "
                    + operation_state.get("projectFile", "")
                )
                return 1

            print("[AE BACKUP REUSED]")
            print(operation_state.get("backupPath", ""))
        else:
            write_text_file(
                run_context.preflight_jsx_path,
                build_preflight_jsx(
                    not args.no_alert,
                    False,
                    run_context.preflight_result_path,
                ),
            )
            try:
                preflight_result = run_afterfx_script(
                    afterfx_com_path,
                    run_context.preflight_jsx_path,
                    run_context.preflight_result_path,
                    "preflight",
                    args.timeout_seconds,
                )
            except RuntimeError as err:
                return fail("[AE ERROR]\n" + str(err))

            if not preflight_result.get("ok"):
                print("[AE ERROR]")
                print(preflight_result.get("message", "Project protection check failed."))
                return 1

            try:
                backup_path = make_backup(preflight_result.get("projectFile", ""))
            except OSError as err:
                return fail("[BACKUP ERROR]\n" + str(err))

            set_operation_state(
                args.operation_id,
                preflight_result.get("projectFile", ""),
                backup_path,
            )

            print("[AE BACKUP]")
            print(str(backup_path))

    write_text_file(
        run_context.wrapper_jsx_path,
        build_wrapper_jsx(jsx_path, run_context),
    )

    print("AE Path: " + str(afterfx_com_path))
    print("JSX Path: " + str(jsx_path))

    try:
        result = run_afterfx_script(
            afterfx_com_path,
            run_context.wrapper_jsx_path,
            run_context.result_path,
            "target script",
            args.timeout_seconds,
            run_context.run_id,
        )
    except RuntimeError as err:
        return fail("[AE ERROR]\n" + str(err))

    if result.get("ok"):
        print("[AE OK]")
        print(result.get("message", "Script executed successfully."))
        print_stage_diagnostics(result)

        if args.capture_frame:
            capture_basename = "frame_capture"
            if args.capture_method == "render-queue":
                capture_jsx = build_render_queue_capture_jsx(
                    capture_basename,
                    args.capture_time_mode,
                    args.capture_time,
                    run_context.frame_capture_result_path,
                    run_context.temp_dir,
                )
            else:
                capture_jsx = build_saveframe_8bpc_capture_jsx(
                    capture_basename,
                    args.capture_time_mode,
                    args.capture_time,
                    run_context.frame_capture_result_path,
                    run_context.temp_dir,
                )
            write_text_file(
                run_context.frame_capture_jsx_path,
                capture_jsx,
            )
            try:
                capture_result = run_afterfx_script(
                    afterfx_com_path,
                    run_context.frame_capture_jsx_path,
                    run_context.frame_capture_result_path,
                    "frame capture",
                    args.timeout_seconds,
                )
            except RuntimeError as err:
                return fail("[AE CAPTURE ERROR]\n" + str(err))

            if not capture_result.get("ok"):
                print("[AE CAPTURE ERROR]")
                print(capture_result.get("message", "Frame capture failed."))
                return 1

            try:
                capture_result = normalize_capture(
                    capture_result,
                    args.capture_max_edge,
                    run_context.frame_capture_result_path,
                    run_context.frame_preview_path,
                )
            except OSError as err:
                return fail("[AE CAPTURE ERROR]\n" + str(err))

            print("[AE CAPTURE OK]")
            print("Method: " + capture_result.get("method", ""))
            print("Comp: " + capture_result.get("compName", ""))
            print("Time: " + str(capture_result.get("time", "")))
            print("Output: " + capture_result.get("outputPath", ""))
            print("Preview: " + capture_result.get("previewPath", ""))
            print_stage_diagnostics(capture_result)
            if capture_result.get("dirtyChangedByCapture"):
                print("[AE CAPTURE WARNING]")
                print("Frame capture restored transient settings but marked the project dirty.")

        if args.capture_video:
            run_context.video_capture_dir.mkdir(parents=True, exist_ok=False)
            capture_jsx = build_saveframe_8bpc_sequence_capture_jsx(
                run_context.video_capture_dir,
                args.capture_video_fps,
                args.capture_video_max_frames,
                run_context.video_capture_result_path,
            )
            write_text_file(run_context.video_capture_jsx_path, capture_jsx)
            try:
                video_timeout = max(
                    args.timeout_seconds,
                    (args.capture_video_max_frames or 120) * 2,
                )
                video_result = run_afterfx_script(
                    afterfx_com_path,
                    run_context.video_capture_jsx_path,
                    run_context.video_capture_result_path,
                    "video capture",
                    video_timeout,
                )
            except RuntimeError as err:
                return fail("[AE VIDEO CAPTURE ERROR]\n" + str(err))

            if not video_result.get("ok"):
                print("[AE VIDEO CAPTURE ERROR]")
                print(video_result.get("message", "Video capture failed."))
                return 1

            try:
                video_result = normalize_video_capture(
                    video_result,
                    args.capture_video_max_edge,
                    args.capture_video_fps,
                    run_context.video_capture_result_path,
                )
            except (OSError, RuntimeError, ValueError) as err:
                return fail("[AE VIDEO CAPTURE ERROR]\n" + str(err))

            print("[AE VIDEO CAPTURE OK]")
            print("Method: " + video_result.get("method", ""))
            print("Comp: " + video_result.get("compName", ""))
            print("Frames: " + str(video_result.get("frameCount", "")))
            print("FPS: " + str(video_result.get("playbackFps", "")))
            print("Output Dir: " + video_result.get("outputDir", ""))
            if video_result.get("videoPath"):
                print("Video: " + video_result.get("videoPath", ""))
            if video_result.get("contactSheetPath"):
                print("Contact Sheet: " + video_result.get("contactSheetPath", ""))
            print_stage_diagnostics(video_result)
            if video_result.get("videoWarning"):
                print("[AE VIDEO CAPTURE WARNING]")
                print(video_result.get("videoWarning", ""))
            if video_result.get("dirtyChangedByCapture"):
                print("[AE VIDEO CAPTURE WARNING]")
                print("Video capture restored transient settings but marked the project dirty.")
        return 0

    print("[AE ERROR]")
    print(result.get("message", "Unknown AE script error."))
    if "line" in result:
        print("Line: " + str(result["line"]))
    print_stage_diagnostics(result)
    return 1


if __name__ == "__main__":
    sys.exit(main())
