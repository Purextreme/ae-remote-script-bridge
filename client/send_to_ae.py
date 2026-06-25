import json
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
RESULT_PATH = PROJECT_ROOT / "logs" / "latest_result.json"
TEMP_DIR = PROJECT_ROOT / "temp"
TIMEOUT_SECONDS = 20


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


def load_afterfx_path():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "Missing config.json. Expected: " + str(CONFIG_PATH)
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    afterfx_com_path = config.get("afterfx_com_path")
    if not afterfx_com_path:
        raise ValueError("config.json must contain afterfx_com_path.")

    return Path(afterfx_com_path)


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


def wait_for_result():
    deadline = time.time() + TIMEOUT_SECONDS
    while time.time() < deadline:
        if RESULT_PATH.exists():
            with RESULT_PATH.open("r", encoding="utf-8-sig") as result_file:
                return json.load(result_file)
        time.sleep(0.2)
    return None


def main():
    if len(sys.argv) != 2:
        return fail("Usage: python client\\send_to_ae.py path\\to\\script.jsx")

    try:
        afterfx_com_path = load_afterfx_path()
    except (OSError, ValueError, json.JSONDecodeError) as err:
        return fail("[CONFIG ERROR]\n" + str(err))

    if not afterfx_com_path.exists():
        return fail(
            "[CONFIG ERROR]\nAfterFX.com not found: " + str(afterfx_com_path)
        )

    jsx_path = Path(sys.argv[1])
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
    if RESULT_PATH.exists():
        RESULT_PATH.unlink()

    wrapper_path = TEMP_DIR / "ae_bridge_wrapper.jsx"
    wrapper_path.write_text(build_wrapper_jsx(jsx_path), encoding="utf-8")

    print("AE Path: " + str(afterfx_com_path))
    print("JSX Path: " + str(jsx_path))

    subprocess.run([str(afterfx_com_path), "-r", str(wrapper_path)])

    try:
        result = wait_for_result()
    except (OSError, json.JSONDecodeError) as err:
        return fail("[AE ERROR]\nCould not read result file: " + str(err))

    if result is None:
        print("[AE TIMEOUT]")
        print("No result file generated.")
        return 1

    if result.get("ok"):
        print("[AE OK]")
        print(result.get("message", "Script executed successfully."))
        return 0

    print("[AE ERROR]")
    print(result.get("message", "Unknown AE script error."))
    if "line" in result:
        print("Line: " + str(result["line"]))
    return 1


if __name__ == "__main__":
    sys.exit(main())
