"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const callback_1 = require("./callback");
const templating_1 = require("../../core/util/templating");
const p = require("../../core/properties");
class OpenURL extends callback_1.Callback {
    constructor(attrs) {
        super(attrs);
    }
    static init_OpenURL() {
        this.define({
            url: [p.String, 'http://'],
            same_tab: [p.Boolean, false],
        });
    }
    execute(_cb_obj, { source }) {
        const open_url = (i) => {
            const url = templating_1.replace_placeholders(this.url, source, i);
            if (this.same_tab)
                window.location.href = url;
            else
                window.open(url);
        };
        const { selected } = source;
        for (const i of selected.indices)
            open_url(i);
        for (const i of selected.line_indices)
            open_url(i);
        // TODO: multiline_indices: {[key: string]: number[]}
    }
}
exports.OpenURL = OpenURL;
OpenURL.__name__ = "OpenURL";
OpenURL.init_OpenURL();
