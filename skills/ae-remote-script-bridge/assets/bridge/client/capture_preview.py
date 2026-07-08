import datetime as dt
import json
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CAPTURE_RESULT_PATH = PROJECT_ROOT / "logs" / "frame_capture_result.json"
VIDEO_CAPTURE_RESULT_PATH = PROJECT_ROOT / "logs" / "video_capture_result.json"
TEMP_DIR = PROJECT_ROOT / "temp"
DEFAULT_CAPTURE_MAX_EDGE = 1500
DEFAULT_VIDEO_CAPTURE_MAX_EDGE = 960
DEFAULT_VIDEO_CAPTURE_FPS = 4.0
DEFAULT_VIDEO_CAPTURE_MAX_FRAMES = 48
MAX_VIDEO_CAPTURE_RUNS = 10


def to_extendscript_path(path):
    return str(path.resolve()).replace("\\", "/")


def escape_extendscript_string(value):
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
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


def build_saveframe_8bpc_sequence_capture_jsx(
    capture_dir, capture_fps, max_frames
):
    result_path = escape_extendscript_string(
        to_extendscript_path(VIDEO_CAPTURE_RESULT_PATH)
    )
    output_dir = escape_extendscript_string(to_extendscript_path(capture_dir))

    return """(function () {
    var resultFile = new File("%s");
    var outputFolder = new Folder("%s");
    var captureFps = %s;
    var maxFrames = %s;
    var startedDirty = false;
    var originalBits = 0;
    var restoredBits = 0;
    var originalTime = 0;
    var framePaths = [];
    var frameTimes = [];

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

    function padFrameNumber(value) {
        var text = String(value);
        while (text.length < 4) {
            text = "0" + text;
        }
        return text;
    }

    function fileExists(path) {
        return (new File(path)).exists;
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

    function writeNumberArray(name, values) {
        var i;
        resultFile.write(',"' + name + '":[');
        for (i = 0; i < values.length; i += 1) {
            if (i > 0) {
                resultFile.write(",");
            }
            resultFile.write(values[i]);
        }
        resultFile.write("]");
    }

    function writeResult(ok, message, comp) {
        resultFile.encoding = "UTF-8";
        resultFile.open("w");
        resultFile.write("{");
        resultFile.write('"ok":' + (ok ? "true" : "false"));
        resultFile.write(',"message":' + quoted(message));
        resultFile.write(',"method":"saveFrameToPng8BpcSequence"');
        resultFile.write(',"fidelity":"preview"');
        resultFile.write(',"compName":' + quoted(comp ? comp.name : ""));
        resultFile.write(',"duration":' + (comp ? comp.duration : 0));
        resultFile.write(',"width":' + (comp ? comp.width : 0));
        resultFile.write(',"height":' + (comp ? comp.height : 0));
        resultFile.write(',"frameDuration":' + (comp ? comp.frameDuration : 0));
        resultFile.write(',"outputDir":' + quoted(outputFolder.fsName));
        resultFile.write(',"captureFps":' + captureFps);
        resultFile.write(',"requestedMaxFrames":' + maxFrames);
        resultFile.write(',"frameCount":' + framePaths.length);
        resultFile.write(',"originalBitsPerChannel":' + originalBits);
        resultFile.write(',"captureBitsPerChannel":8');
        resultFile.write(',"restoredBitsPerChannel":' + restoredBits);
        resultFile.write(',"startedDirty":' + (startedDirty ? "true" : "false"));
        resultFile.write(',"endedDirty":' + (app.project && app.project.dirty ? "true" : "false"));
        resultFile.write(',"dirtyChangedByCapture":' + (!startedDirty && app.project && app.project.dirty ? "true" : "false"));
        writeStringArray("framePaths", framePaths);
        writeNumberArray("frameTimes", frameTimes);
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

    function chooseFrameCount(comp) {
        var count = Math.floor(comp.duration * captureFps) + 1;
        if (count < 1) {
            count = 1;
        }
        if (maxFrames > 0 && count > maxFrames) {
            count = maxFrames;
        }
        return count;
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
        if (captureFps <= 0) {
            throw new Error("captureFps must be greater than 0.");
        }

        if (!outputFolder.exists) {
            outputFolder.create();
        }

        originalTime = comp.time;
        app.project.bitsPerChannel = 8;
        comp.openInViewer();

        var frameCount = chooseFrameCount(comp);
        var start = comp.displayStartTime || 0;
        var end = start + comp.duration - comp.frameDuration;
        if (end < start) {
            end = start;
        }

        var i;
        for (i = 0; i < frameCount; i += 1) {
            var captureTime = start;
            if (frameCount > 1) {
                captureTime = start + ((end - start) * i / (frameCount - 1));
            }
            captureTime = clampTime(comp, captureTime);

            var outputFile = new File(outputFolder.fsName + "/frame_" + padFrameNumber(i + 1) + ".png");
            if (outputFile.exists) {
                outputFile.remove();
            }

            comp.time = captureTime;
            comp.saveFrameToPng(captureTime, outputFile);

            if (!waitForFile(outputFile.fsName)) {
                throw new Error("saveFrameToPng returned but frame output was not found: " + outputFile.fsName);
            }

            framePaths.push(outputFile.fsName);
            frameTimes.push(captureTime);
        }

        app.project.bitsPerChannel = originalBits;
        restoredBits = app.project.bitsPerChannel;
        comp.time = originalTime;
        writeResult(true, "Preview frame sequence captured successfully.", comp);
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
        writeResult(false, err.toString() + " Line: " + (err.line || 0), null);
    }
})();""" % (
        result_path,
        output_dir,
        float(capture_fps),
        int(max_frames),
    )


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

def path_is_inside(path, parent):
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def prune_video_capture_runs(keep_runs):
    root = TEMP_DIR / "preview_videos"
    root.mkdir(parents=True, exist_ok=True)
    if keep_runs < 1:
        keep_runs = 1

    runs = [
        path
        for path in root.iterdir()
        if path.is_dir() and path.name.startswith("video_capture_")
    ]
    runs.sort(key=lambda path: path.stat().st_mtime, reverse=True)

    for stale_run in runs[keep_runs:]:
        if path_is_inside(stale_run, root):
            shutil.rmtree(stale_run)


def create_video_capture_dir():
    root = TEMP_DIR / "preview_videos"
    root.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    capture_dir = root / ("video_capture_" + timestamp)
    capture_dir.mkdir(parents=False, exist_ok=False)
    return capture_dir


def resize_video_frame(source_path, dest_path, max_edge):
    from PIL import Image

    with Image.open(source_path) as image:
        image = image.convert("RGBA")
        if max_edge > 0:
            image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
        if image.width % 2 or image.height % 2:
            even_width = image.width + (image.width % 2)
            even_height = image.height + (image.height % 2)
            canvas = Image.new("RGBA", (even_width, even_height), (0, 0, 0, 255))
            canvas.paste(image, (0, 0))
            image = canvas
        image.convert("RGB").save(dest_path)


def make_contact_sheet(frame_paths, frame_times, contact_sheet_path):
    from PIL import Image, ImageDraw

    if not frame_paths:
        raise ValueError("No preview frames available for contact sheet.")

    columns = 6
    rows = (len(frame_paths) + columns - 1) // columns
    label_height = 22
    padding = 6

    with Image.open(frame_paths[0]) as first_image:
        cell_width = first_image.width
        cell_height = first_image.height + label_height

    sheet_width = columns * cell_width + (columns + 1) * padding
    sheet_height = rows * cell_height + (rows + 1) * padding
    sheet = Image.new("RGB", (sheet_width, sheet_height), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)

    for index, frame_path in enumerate(frame_paths):
        column = index % columns
        row = index // columns
        x = padding + column * (cell_width + padding)
        y = padding + row * (cell_height + padding)
        with Image.open(frame_path) as frame:
            sheet.paste(frame.convert("RGB"), (x, y))
        label = "#" + str(index + 1) + "  " + ("%.2fs" % frame_times[index])
        draw.text((x + 4, y + cell_height - label_height + 4), label, fill=(230, 230, 230))

    sheet.save(contact_sheet_path)


def assemble_preview_video(video_path, playback_fps):
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        return "ffmpeg was not found; MP4 preview was not generated."

    input_pattern = str(video_path.parent / "frame_%04d.png")
    command = [
        ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-framerate",
        str(float(playback_fps)),
        "-i",
        input_pattern,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(video_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        return "ffmpeg failed: " + (result.stderr.strip() or "unknown error")
    return ""


def normalize_video_capture(capture_result, max_edge, playback_fps):
    frame_paths = [Path(path) for path in capture_result.get("framePaths", [])]
    frame_times = capture_result.get("frameTimes", [])
    if not frame_paths:
        raise FileNotFoundError("No captured preview frames were reported.")
    for frame_path in frame_paths:
        if not frame_path.exists():
            raise FileNotFoundError("Captured preview frame not found: " + str(frame_path))

    output_dir = Path(capture_result.get("outputDir", ""))
    preview_dir = output_dir / "preview"
    preview_dir.mkdir(parents=True, exist_ok=True)

    resized_paths = []
    try:
        for index, frame_path in enumerate(frame_paths):
            resized_path = preview_dir / ("frame_" + str(index + 1).zfill(4) + ".png")
            resize_video_frame(frame_path, resized_path, max_edge)
            resized_paths.append(resized_path)

        contact_sheet_path = output_dir / "preview_contact_sheet.png"
        make_contact_sheet(resized_paths, frame_times, contact_sheet_path)
    except ImportError:
        raise RuntimeError(
            "Pillow is required to create video previews. Install Pillow or use --capture-frame."
        )

    video_path = preview_dir / "preview.mp4"
    video_warning = assemble_preview_video(video_path, playback_fps)

    latest_contact_sheet = TEMP_DIR / "latest_video_capture_contact_sheet.png"
    shutil.copy2(contact_sheet_path, latest_contact_sheet)

    capture_result["previewDir"] = str(preview_dir)
    capture_result["contactSheetPath"] = str(contact_sheet_path)
    capture_result["latestContactSheetPath"] = str(latest_contact_sheet)
    capture_result["playbackFps"] = playback_fps
    capture_result["previewMaxEdge"] = max_edge
    if video_warning:
        capture_result["videoWarning"] = video_warning
    else:
        latest_video = TEMP_DIR / "latest_video_capture_preview.mp4"
        shutil.copy2(video_path, latest_video)
        capture_result["videoPath"] = str(video_path)
        capture_result["latestVideoPath"] = str(latest_video)

    VIDEO_CAPTURE_RESULT_PATH.write_text(
        json.dumps(capture_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return capture_result
