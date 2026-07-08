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


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
RESULT_PATH = PROJECT_ROOT / "logs" / "latest_result.json"
PREFLIGHT_RESULT_PATH = PROJECT_ROOT / "logs" / "preflight_result.json"
CAPTURE_RESULT_PATH = PROJECT_ROOT / "logs" / "frame_capture_result.json"
PROTECTION_STATE_PATH = PROJECT_ROOT / "logs" / "protection_state.json"
TEMP_DIR = PROJECT_ROOT / "temp"
TIMEOUT_SECONDS = 20
DEFAULT_ADOBE_DIR = Path("C:/Program Files/Adobe")
BACKUP_PREFIX = "agent backup"
BACKUP_DIR_NAME = "agent backups"
MAX_BACKUPS = 10
DEFAULT_CAPTURE_MAX_EDGE = 1500


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


def build_wrapper_jsx(target_jsx):
    target_path = escape_extendscript_string(to_extendscript_path(target_jsx))
    bridge_root = escape_extendscript_string(to_extendscript_path(PROJECT_ROOT))
    logs_dir = escape_extendscript_string(to_extendscript_path(RESULT_PATH.parent))
    temp_dir = escape_extendscript_string(to_extendscript_path(TEMP_DIR))
    result_path = escape_extendscript_string(to_extendscript_path(RESULT_PATH))

    return """(function () {
    var targetFile = new File("%s");
    var resultFile = new File("%s");
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
        bridge_root,
        logs_dir,
        temp_dir,
        result_path,
    )


def build_preflight_jsx(show_alert, allow_dirty):
    result_path = escape_extendscript_string(
        to_extendscript_path(PREFLIGHT_RESULT_PATH)
    )

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


def build_saveframe_8bpc_capture_jsx(capture_basename, time_mode, capture_time):
    result_path = escape_extendscript_string(to_extendscript_path(CAPTURE_RESULT_PATH))
    output_path = escape_extendscript_string(
        to_extendscript_path(TEMP_DIR / (capture_basename + ".png"))
    )
    capture_time_text = "null" if capture_time is None else str(float(capture_time))

    return """(function () {
    var resultFile = new File("%s");
    var outputFile = new File("%s");
    var timeMode = "%s";
    var requestedTime = %s;
    var startedDirty = false;
    var originalBits = 0;
    var restoredBits = 0;
    var originalTime = 0;

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

    function fileExists(path) {
        return (new File(path)).exists;
    }

    function removeFile(path) {
        var file = new File(path);
        if (file.exists) {
            file.remove();
        }
    }

    function waitForFile(path) {
        var deadline = new Date().getTime() + 8000;
        while (new Date().getTime() < deadline) {
            if (fileExists(path)) {
                return true;
            }
            $.sleep(100);
        }
        return false;
    }

    function writeResult(ok, message, comp, captureTime, outputPath) {
        resultFile.encoding = "UTF-8";
        resultFile.open("w");
        resultFile.write("{");
        resultFile.write('"ok":' + (ok ? "true" : "false"));
        resultFile.write(',"message":' + quoted(message));
        resultFile.write(',"method":"saveFrameToPng8Bpc"');
        resultFile.write(',"fidelity":"preview"');
        resultFile.write(',"compName":' + quoted(comp ? comp.name : ""));
        resultFile.write(',"time":' + (captureTime !== null && captureTime !== undefined ? captureTime : 0));
        resultFile.write(',"outputPath":' + quoted(outputPath || ""));
        resultFile.write(',"outputExists":' + (outputPath && fileExists(outputPath) ? "true" : "false"));
        resultFile.write(',"originalBitsPerChannel":' + originalBits);
        resultFile.write(',"captureBitsPerChannel":8');
        resultFile.write(',"restoredBitsPerChannel":' + restoredBits);
        resultFile.write(',"startedDirty":' + (startedDirty ? "true" : "false"));
        resultFile.write(',"endedDirty":' + (app.project && app.project.dirty ? "true" : "false"));
        resultFile.write(',"dirtyChangedByCapture":' + (!startedDirty && app.project && app.project.dirty ? "true" : "false"));
        resultFile.write("}");
        resultFile.close();
    }

    function clampTime(comp, value) {
        var start = comp.displayStartTime || 0;
        var end = start + comp.duration - comp.frameDuration;
        if (end < start) {
            end = start;
        }
        if (value < start) {
            return start;
        }
        if (value > end) {
            return end;
        }
        return value;
    }

    function chooseTime(comp) {
        var start = comp.displayStartTime || 0;
        if (requestedTime !== null) {
            return clampTime(comp, requestedTime);
        }
        if (timeMode === "middle") {
            return clampTime(comp, start + comp.duration * 0.5);
        }
        if (timeMode === "two-thirds") {
            return clampTime(comp, start + comp.duration * 0.6666667);
        }
        if (timeMode === "end") {
            return clampTime(comp, start + comp.duration - comp.frameDuration);
        }
        return clampTime(comp, comp.time);
    }

    try {
        if (!app.project) {
            throw new Error("No open After Effects project.");
        }

        startedDirty = !!app.project.dirty;
        originalBits = app.project.bitsPerChannel;

        var comp = app.project.activeItem;
        if (!(comp instanceof CompItem)) {
            throw new Error("Active item is not a composition. Open or select the composition to capture.");
        }
        if (typeof comp.saveFrameToPng !== "function") {
            throw new Error("saveFrameToPng is not available in this After Effects version.");
        }

        originalTime = comp.time;
        var captureTime = chooseTime(comp);
        removeFile(outputFile.fsName);

        app.project.bitsPerChannel = 8;
        comp.time = captureTime;
        comp.openInViewer();
        comp.saveFrameToPng(captureTime, outputFile);

        if (!waitForFile(outputFile.fsName)) {
            app.project.bitsPerChannel = originalBits;
            restoredBits = app.project.bitsPerChannel;
            comp.time = originalTime;
            writeResult(false, "saveFrameToPng returned but no PNG output was found.", comp, captureTime, outputFile.fsName);
            return;
        }

        app.project.bitsPerChannel = originalBits;
        restoredBits = app.project.bitsPerChannel;
        comp.time = originalTime;
        writeResult(true, "Frame captured successfully.", comp, captureTime, outputFile.fsName);
    } catch (err) {
        try {
            app.project.bitsPerChannel = originalBits;
            restoredBits = app.project.bitsPerChannel;
            var activeComp = app.project.activeItem;
            if (activeComp instanceof CompItem) {
                activeComp.time = originalTime;
            }
        } catch (restoreErr) {
        }
        writeResult(false, err.toString() + " Line: " + (err.line || 0), null, 0, "");
    }
})();""" % (
        result_path,
        output_path,
        escape_extendscript_string(time_mode),
        capture_time_text,
    )


def build_render_queue_capture_jsx(capture_basename, time_mode, capture_time):
    result_path = escape_extendscript_string(to_extendscript_path(CAPTURE_RESULT_PATH))
    output_base = escape_extendscript_string(
        to_extendscript_path(TEMP_DIR / (capture_basename + ".png"))
    )
    capture_time_text = "null" if capture_time is None else str(float(capture_time))

    return """(function () {
    var resultFile = new File("%s");
    var outputBase = new File("%s");
    var timeMode = "%s";
    var requestedTime = %s;
    var captureItem = null;
    var disabledItems = [];
    var disabledNames = [];
    var queueRestored = false;
    var captureItemRemoved = false;
    var startedDirty = false;

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

    function fileExists(path) {
        return (new File(path)).exists;
    }

    function removeFile(path) {
        var file = new File(path);
        if (file.exists) {
            file.remove();
        }
    }

    function writeStringArray(name, values) {
        var i;
        resultFile.write(',"' + name + '":[');
        for (i = 0; i < values.length; i += 1) {
            if (i > 0) {
                resultFile.write(",");
            }
            resultFile.write(quoted(values[i]));
        }
        resultFile.write("]");
    }

    function writeResult(ok, message, comp, captureTime, outputPath) {
        resultFile.encoding = "UTF-8";
        resultFile.open("w");
        resultFile.write("{");
        resultFile.write('"ok":' + (ok ? "true" : "false"));
        resultFile.write(',"message":' + quoted(message));
        resultFile.write(',"method":"isolatedRenderQueue"');
        resultFile.write(',"compName":' + quoted(comp ? comp.name : ""));
        resultFile.write(',"time":' + (captureTime !== null && captureTime !== undefined ? captureTime : 0));
        resultFile.write(',"outputPath":' + quoted(outputPath || ""));
        resultFile.write(',"outputExists":' + (outputPath && fileExists(outputPath) ? "true" : "false"));
        resultFile.write(',"queueRestored":' + (queueRestored ? "true" : "false"));
        resultFile.write(',"captureItemRemoved":' + (captureItemRemoved ? "true" : "false"));
        resultFile.write(',"startedDirty":' + (startedDirty ? "true" : "false"));
        resultFile.write(',"endedDirty":' + (app.project && app.project.dirty ? "true" : "false"));
        resultFile.write(',"dirtyChangedByCapture":' + (!startedDirty && app.project && app.project.dirty ? "true" : "false"));
        writeStringArray("disabledItems", disabledNames);
        resultFile.write("}");
        resultFile.close();
    }

    function restoreDisabledItems() {
        var i;
        for (i = 0; i < disabledItems.length; i += 1) {
            try {
                disabledItems[i].render = true;
            } catch (restoreErr) {
            }
        }
        queueRestored = true;
    }

    function removeCaptureItem() {
        if (captureItem) {
            try {
                captureItem.remove();
            } catch (removeErr) {
            }
            captureItem = null;
        }
        captureItemRemoved = true;
    }

    function clampTime(comp, value) {
        var start = comp.displayStartTime || 0;
        var end = start + comp.duration - comp.frameDuration;
        if (end < start) {
            end = start;
        }
        if (value < start) {
            return start;
        }
        if (value > end) {
            return end;
        }
        return value;
    }

    function chooseTime(comp) {
        var start = comp.displayStartTime || 0;
        if (requestedTime !== null) {
            return clampTime(comp, requestedTime);
        }
        if (timeMode === "middle") {
            return clampTime(comp, start + comp.duration * 0.5);
        }
        if (timeMode === "two-thirds") {
            return clampTime(comp, start + comp.duration * 0.6666667);
        }
        if (timeMode === "end") {
            return clampTime(comp, start + comp.duration - comp.frameDuration);
        }
        return clampTime(comp, comp.time);
    }

    function findOutputFile() {
        var base = outputBase.fsName;
        var candidates = [
            base,
            base + "00000",
            base.replace(/\\.png$/i, "_00000.png"),
            base.replace(/\\.png$/i, "_[00000].png")
        ];
        var i;
        for (i = 0; i < candidates.length; i += 1) {
            if (fileExists(candidates[i])) {
                return candidates[i];
            }
        }

        var matches = outputBase.parent.getFiles(outputBase.name + "*");
        if (matches.length > 0) {
            return matches[0].fsName;
        }
        return "";
    }

    try {
        if (!app.project) {
            throw new Error("No open After Effects project.");
        }
        if (app.project.renderQueue.rendering) {
            throw new Error("Render Queue is currently rendering. Cannot safely capture a frame.");
        }
        startedDirty = !!app.project.dirty;

        var comp = app.project.activeItem;
        if (!(comp instanceof CompItem)) {
            throw new Error("Active item is not a composition. Open or select the composition to capture.");
        }

        removeFile(outputBase.fsName);
        removeFile(outputBase.fsName + "00000");
        removeFile(outputBase.fsName.replace(/\\.png$/i, "_00000.png"));
        removeFile(outputBase.fsName.replace(/\\.png$/i, "_[00000].png"));

        var captureTime = chooseTime(comp);
        comp.time = captureTime;
        comp.openInViewer();

        var i;
        for (i = 1; i <= app.project.renderQueue.numItems; i += 1) {
            var rqItem = app.project.renderQueue.item(i);
            if (rqItem.render && rqItem.status === RQItemStatus.QUEUED) {
                rqItem.render = false;
                disabledItems.push(rqItem);
                disabledNames.push(rqItem.comp ? rqItem.comp.name : "Unknown");
            }
        }

        captureItem = app.project.renderQueue.items.add(comp);
        captureItem.applyTemplate("Best Settings");
        captureItem.timeSpanStart = captureTime;
        captureItem.timeSpanDuration = comp.frameDuration;
        captureItem.outputModule(1).applyTemplate("PNG");
        captureItem.outputModule(1).file = outputBase;
        captureItem.render = true;

        app.project.renderQueue.render();

        var outputPath = findOutputFile();
        removeCaptureItem();
        restoreDisabledItems();

        if (outputPath === "") {
            writeResult(false, "Render Queue completed but no PNG output was found.", comp, captureTime, "");
            return;
        }

        writeResult(true, "Frame captured successfully.", comp, captureTime, outputPath);
    } catch (err) {
        removeCaptureItem();
        restoreDisabledItems();
        writeResult(false, err.toString() + " Line: " + (err.line || 0), null, 0, "");
    }
})();""" % (
        result_path,
        output_base,
        escape_extendscript_string(time_mode),
        capture_time_text,
    )


def wait_for_result(result_path):
    deadline = time.time() + TIMEOUT_SECONDS
    last_error = None
    while time.time() < deadline:
        if result_path.exists():
            try:
                with result_path.open("r", encoding="utf-8-sig") as result_file:
                    return json.load(result_file)
            except json.JSONDecodeError as err:
                last_error = err
        time.sleep(0.2)
    if last_error is not None:
        raise last_error
    return None


def run_afterfx_script(afterfx_com_path, jsx_path, result_path):
    if result_path.exists():
        result_path.unlink()

    subprocess.run([str(afterfx_com_path), "-r", str(jsx_path)])

    try:
        return wait_for_result(result_path)
    except (OSError, json.JSONDecodeError) as err:
        raise RuntimeError("Could not read result file: " + str(err))


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
            return json.load(state_file)
    except (OSError, json.JSONDecodeError):
        return {}


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


def normalize_capture(capture_result, max_edge):
    output_path = Path(capture_result.get("outputPath", ""))
    if not output_path.exists():
        raise FileNotFoundError("Captured frame not found: " + str(output_path))

    preview_path = TEMP_DIR / "latest_frame_capture_preview.png"

    try:
        from PIL import Image
    except ImportError:
        shutil.copy2(output_path, preview_path)
        if max_edge > 0:
            print("[AE CAPTURE WARNING]")
            print("Pillow is not installed; copied full-size capture without resizing.")
        capture_result["previewPath"] = str(preview_path)
        CAPTURE_RESULT_PATH.write_text(
            json.dumps(capture_result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return capture_result

    with Image.open(output_path) as image:
        image = image.copy()
        if max_edge > 0:
            image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
        image.save(preview_path)

    capture_result["previewPath"] = str(preview_path)
    capture_result["previewWidth"] = image.width
    capture_result["previewHeight"] = image.height
    CAPTURE_RESULT_PATH.write_text(
        json.dumps(capture_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return capture_result


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
    args = parser.parse_args()

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

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    if not args.no_protect:
        operation_state = get_operation_state(args.operation_id)
        if operation_state and Path(operation_state.get("backupPath", "")).exists():
            preflight_path = TEMP_DIR / "ae_bridge_preflight.jsx"
            write_text_file(preflight_path, build_preflight_jsx(False, True))
            try:
                preflight_result = run_afterfx_script(
                    afterfx_com_path, preflight_path, PREFLIGHT_RESULT_PATH
                )
            except RuntimeError as err:
                return fail("[AE ERROR]\n" + str(err))

            if preflight_result is None:
                print("[AE TIMEOUT]")
                print("No preflight result file generated.")
                return 1

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
            preflight_path = TEMP_DIR / "ae_bridge_preflight.jsx"
            write_text_file(preflight_path, build_preflight_jsx(not args.no_alert, False))
            try:
                preflight_result = run_afterfx_script(
                    afterfx_com_path, preflight_path, PREFLIGHT_RESULT_PATH
                )
            except RuntimeError as err:
                return fail("[AE ERROR]\n" + str(err))

            if preflight_result is None:
                print("[AE TIMEOUT]")
                print("No preflight result file generated.")
                return 1

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

    wrapper_path = TEMP_DIR / "ae_bridge_wrapper.jsx"
    write_text_file(wrapper_path, build_wrapper_jsx(jsx_path))

    print("AE Path: " + str(afterfx_com_path))
    print("JSX Path: " + str(jsx_path))

    try:
        result = run_afterfx_script(afterfx_com_path, wrapper_path, RESULT_PATH)
    except RuntimeError as err:
        return fail("[AE ERROR]\n" + str(err))

    if result is None:
        print("[AE TIMEOUT]")
        print("No result file generated.")
        return 1

    if result.get("ok"):
        print("[AE OK]")
        print(result.get("message", "Script executed successfully."))

        if args.capture_frame:
            capture_basename = "frame_capture_" + dt.datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )
            capture_path = TEMP_DIR / "ae_bridge_capture_frame.jsx"
            if args.capture_method == "render-queue":
                capture_jsx = build_render_queue_capture_jsx(
                    capture_basename,
                    args.capture_time_mode,
                    args.capture_time,
                )
            else:
                capture_jsx = build_saveframe_8bpc_capture_jsx(
                    capture_basename,
                    args.capture_time_mode,
                    args.capture_time,
                )
            write_text_file(
                capture_path,
                capture_jsx,
            )
            try:
                capture_result = run_afterfx_script(
                    afterfx_com_path, capture_path, CAPTURE_RESULT_PATH
                )
            except RuntimeError as err:
                return fail("[AE CAPTURE ERROR]\n" + str(err))

            if capture_result is None:
                print("[AE CAPTURE TIMEOUT]")
                print("No frame capture result file generated.")
                return 1

            if not capture_result.get("ok"):
                print("[AE CAPTURE ERROR]")
                print(capture_result.get("message", "Frame capture failed."))
                return 1

            try:
                capture_result = normalize_capture(
                    capture_result, args.capture_max_edge
                )
            except OSError as err:
                return fail("[AE CAPTURE ERROR]\n" + str(err))

            print("[AE CAPTURE OK]")
            print("Method: " + capture_result.get("method", ""))
            print("Comp: " + capture_result.get("compName", ""))
            print("Time: " + str(capture_result.get("time", "")))
            print("Output: " + capture_result.get("outputPath", ""))
            print("Preview: " + capture_result.get("previewPath", ""))
            if capture_result.get("dirtyChangedByCapture"):
                print("[AE CAPTURE WARNING]")
                print("Frame capture restored transient settings but marked the project dirty.")
        return 0

    print("[AE ERROR]")
    print(result.get("message", "Unknown AE script error."))
    if "line" in result:
        print("Line: " + str(result["line"]))
    return 1


if __name__ == "__main__":
    sys.exit(main())
