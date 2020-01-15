"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const p = require("../../core/properties");
const widget_1 = require("./widget");
class FileInputView extends widget_1.WidgetView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.change, () => this.render());
        this.connect(this.model.properties.width.change, () => this.render());
    }
    render() {
        if (this.dialogEl) {
            return;
        }
        this.dialogEl = document.createElement('input');
        this.dialogEl.type = "file";
        this.dialogEl.multiple = false;
        if (this.model.accept != null && this.model.accept != '')
            this.dialogEl.accept = this.model.accept;
        this.dialogEl.style.width = `{this.model.width}px`;
        this.dialogEl.onchange = (e) => this.load_file(e);
        this.el.appendChild(this.dialogEl);
    }
    load_file(e) {
        const reader = new FileReader();
        this.model.filename = e.target.files[0].name;
        reader.onload = (e) => this.file(e);
        reader.readAsDataURL(e.target.files[0]);
    }
    file(e) {
        const file = e.target.result;
        const file_arr = file.split(",");
        const content = file_arr[1];
        const header = file_arr[0].split(":")[1].split(";")[0];
        this.model.value = content;
        this.model.mime_type = header;
    }
}
exports.FileInputView = FileInputView;
FileInputView.__name__ = "FileInputView";
class FileInput extends widget_1.Widget {
    constructor(attrs) {
        super(attrs);
    }
    static init_FileInput() {
        this.prototype.default_view = FileInputView;
        this.define({
            value: [p.String, ''],
            mime_type: [p.String, ''],
            filename: [p.String, ''],
            accept: [p.String, ''],
        });
    }
}
exports.FileInput = FileInput;
FileInput.__name__ = "FileInput";
FileInput.init_FileInput();
