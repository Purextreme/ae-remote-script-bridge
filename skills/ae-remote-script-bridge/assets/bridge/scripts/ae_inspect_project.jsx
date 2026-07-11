(function () {
    var logsDir = $.global.AE_BRIDGE_LOGS_DIR;
    if (!logsDir) {
        throw new Error("AE_BRIDGE_LOGS_DIR is missing. Run this script through the AE bridge.");
    }
    var outputFile = new File(logsDir + "/project_structure.json");

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

    function itemKind(item) {
        if (item instanceof CompItem) {
            return "comp";
        }
        if (item instanceof FolderItem) {
            return "folder";
        }
        if (item instanceof FootageItem) {
            return "footage";
        }
        return item.typeName;
    }

    function layerKind(layer) {
        if (layer instanceof TextLayer) {
            return "text";
        }
        if (layer instanceof CameraLayer) {
            return "camera";
        }
        if (layer instanceof LightLayer) {
            return "light";
        }
        if (layer instanceof ShapeLayer) {
            return "shape";
        }
        if (layer instanceof AVLayer) {
            if (layer.source instanceof CompItem) {
                return "precomp";
            }
            if (layer.source instanceof FootageItem) {
                if (layer.source.mainSource instanceof SolidSource) {
                    return "solid";
                }
                return "footage";
            }
        }
        return "layer";
    }

    function textLayerValue(layer) {
        try {
            var textGroup = layer.property("ADBE Text Properties");
            var sourceText = textGroup.property("ADBE Text Document");
            return sourceText.value.text;
        } catch (err) {
            return "";
        }
    }

    function effectCount(layer) {
        try {
            return layer.property("ADBE Effect Parade").numProperties;
        } catch (err) {
            return 0;
        }
    }

    function opacityKeyCount(layer) {
        try {
            return layer.property("ADBE Transform Group").property("ADBE Opacity").numKeys;
        } catch (err) {
            return 0;
        }
    }

    function writeLayer(file, layer) {
        file.write("{");
        file.write('"index":' + layer.index);
        file.write(',"name":' + quoted(layer.name));
        file.write(',"kind":' + quoted(layerKind(layer)));
        file.write(',"enabled":' + (layer.enabled ? "true" : "false"));
        file.write(',"locked":' + (layer.locked ? "true" : "false"));
        file.write(',"startTime":' + layer.startTime);
        file.write(',"inPoint":' + layer.inPoint);
        file.write(',"outPoint":' + layer.outPoint);
        file.write(',"effectCount":' + effectCount(layer));
        file.write(',"opacityKeyCount":' + opacityKeyCount(layer));
        if (layer instanceof TextLayer) {
            file.write(',"text":' + quoted(textLayerValue(layer)));
        }
        if (layer instanceof AVLayer && layer.source !== null) {
            file.write(',"sourceName":' + quoted(layer.source.name));
        }
        file.write("}");
    }

    function writeItem(file, item, itemIndex) {
        var j;

        file.write("{");
        file.write('"index":' + itemIndex);
        file.write(',"name":' + quoted(item.name));
        file.write(',"kind":' + quoted(itemKind(item)));
        file.write(',"parentFolder":' + quoted(item.parentFolder ? item.parentFolder.name : ""));

        if (item instanceof CompItem) {
            file.write(',"width":' + item.width);
            file.write(',"height":' + item.height);
            file.write(',"duration":' + item.duration);
            file.write(',"frameRate":' + item.frameRate);
            file.write(',"bgColor":[' + item.bgColor[0] + "," + item.bgColor[1] + "," + item.bgColor[2] + "]");
            file.write(',"layers":[');
            for (j = 1; j <= item.numLayers; j += 1) {
                if (j > 1) {
                    file.write(",");
                }
                writeLayer(file, item.layer(j));
            }
            file.write("]");
        }

        file.write("}");
    }

    outputFile.encoding = "UTF-8";
    outputFile.open("w");
    outputFile.write("{");
    outputFile.write('"projectFile":' + quoted(app.project.file ? app.project.file.fsName : ""));
    outputFile.write(',"numItems":' + app.project.numItems);
    outputFile.write(',"activeItem":' + quoted(app.project.activeItem ? app.project.activeItem.name : ""));
    outputFile.write(',"items":[');

    for (var i = 1; i <= app.project.numItems; i += 1) {
        if (i > 1) {
            outputFile.write(",");
        }
        writeItem(outputFile, app.project.item(i), i);
    }

    outputFile.write("]}");
    outputFile.close();
})();
