(function () {
    var rootPath = $.global.AE_BRIDGE_ROOT || "D:/YANQ/AI_Explorer/AE_remote_script_bridge";
    var logsDir = $.global.AE_BRIDGE_LOGS_DIR || (rootPath + "/logs");
    var tempDir = $.global.AE_BRIDGE_TEMP_DIR || (rootPath + "/temp");
    var reportFile = new File(logsDir + "/integration_test_result.json");
    var outputFile = new File(tempDir + "/ae_bridge_render_test.mp4");
    var projectFile = new File(tempDir + "/ae_bridge_integration_test.aep");
    var folderName = "AE_Bridge_Integration_Folder";
    var compName = "AE_Bridge_Integration_Comp_Renamed";
    var setupUndoStarted = false;
    var report = [];
    var comp = null;
    var folder = null;
    var solid = null;

    function escapeJson(value) {
        var text = String(value);
        text = text.replace(/\\/g, "\\\\");
        text = text.replace(/"/g, '\\"');
        text = text.replace(/\r/g, "\\r");
        text = text.replace(/\n/g, "\\n");
        text = text.replace(/\t/g, "\\t");
        return text;
    }

    function quoted(value) {
        return '"' + escapeJson(value) + '"';
    }

    function addCheck(name, ok, detail) {
        report.push({
            name: name,
            ok: ok,
            detail: detail
        });
    }

    function writeReport(ok, message) {
        var i;

        reportFile.encoding = "UTF-8";
        reportFile.open("w");
        reportFile.write("{");
        reportFile.write('"ok":' + (ok ? "true" : "false"));
        reportFile.write(',"message":' + quoted(message));
        reportFile.write(',"projectFile":' + quoted(projectFile.fsName));
        reportFile.write(',"outputFile":' + quoted(outputFile.fsName));
        reportFile.write(',"checks":[');

        for (i = 0; i < report.length; i += 1) {
            if (i > 0) {
                reportFile.write(",");
            }
            reportFile.write("{");
            reportFile.write('"name":' + quoted(report[i].name));
            reportFile.write(',"ok":' + (report[i].ok ? "true" : "false"));
            reportFile.write(',"detail":' + quoted(report[i].detail));
            reportFile.write("}");
        }

        reportFile.write("]}");
        reportFile.close();
    }

    function removeExistingIntegrationItems() {
        var i;
        var item;

        for (i = app.project.numItems; i >= 1; i -= 1) {
            item = app.project.item(i);
            if (
                item.name === folderName ||
                item.name === compName ||
                item.name === "AE_Bridge_Integration_Comp" ||
                item.name === "AE_Bridge_Integration_Solid"
            ) {
                item.remove();
            }
        }
    }

    var oldAviFile = new File(tempDir + "/ae_bridge_render_test.avi");
    if (oldAviFile.exists) {
        oldAviFile.remove();
    }
    if (outputFile.exists) {
        outputFile.remove();
    }

    app.beginUndoGroup("AE Bridge Integration Ops Test");
    setupUndoStarted = true;

    try {
        removeExistingIntegrationItems();

        folder = app.project.items.addFolder(folderName);
        addCheck("create folder", folder instanceof FolderItem, folder.name);

        comp = app.project.items.addComp(
            "AE_Bridge_Integration_Comp",
            320,
            180,
            1,
            0.5,
            12
        );
        comp.name = compName;
        comp.parentFolder = folder;
        addCheck(
            "create move rename comp",
            comp.name === compName && comp.parentFolder === folder,
            comp.name + " in " + comp.parentFolder.name
        );

        solid = comp.layers.addSolid(
            [0.2, 0.45, 0.85],
            "AE_Bridge_Integration_Solid",
            320,
            180,
            1,
            0.5
        );

        var effects = solid.property("ADBE Effect Parade");
        var blur = effects.addProperty("ADBE Gaussian Blur 2");
        addCheck(
            "add effect",
            effects.numProperties === 1 && blur !== null,
            "effect count after add: " + effects.numProperties
        );
        blur.remove();
        addCheck(
            "delete effect",
            effects.numProperties === 0,
            "effect count after delete: " + effects.numProperties
        );

        var opacity = solid.property("ADBE Transform Group").property("ADBE Opacity");
        opacity.setValueAtTime(0, 0);
        opacity.setValueAtTime(0.25, 35);
        addCheck(
            "create keyframes",
            opacity.numKeys === 2,
            "opacity keys after add: " + opacity.numKeys
        );
        while (opacity.numKeys > 0) {
            opacity.removeKey(opacity.numKeys);
        }
        addCheck(
            "delete keyframes",
            opacity.numKeys === 0,
            "opacity keys after delete: " + opacity.numKeys
        );

        setupUndoStarted = false;
        app.endUndoGroup();

        var rqItem = app.project.renderQueue.items.add(comp);
        rqItem.outputModule(1).file = outputFile;
        outputFile = rqItem.outputModule(1).file;
        addCheck(
            "create output",
            outputFile !== null,
            outputFile ? outputFile.fsName : "missing output file setting"
        );

        app.project.renderQueue.render();
        addCheck(
            "render output",
            outputFile.exists,
            outputFile.exists ? outputFile.fsName : "missing output file"
        );

        app.project.save(projectFile);
        addCheck(
            "save project",
            projectFile.exists,
            projectFile.exists ? projectFile.fsName : "missing project file"
        );

        writeReport(true, "Integration operations completed.");
    } catch (err) {
        if (setupUndoStarted) {
            app.endUndoGroup();
        }
        writeReport(false, err.toString() + " Line: " + err.line);
        throw err;
    }
})();
