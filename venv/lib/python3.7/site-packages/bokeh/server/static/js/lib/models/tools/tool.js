"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const p = require("../../core/properties");
const view_1 = require("../../core/view");
const array_1 = require("../../core/util/array");
const model_1 = require("../../model");
class ToolView extends view_1.View {
    get plot_view() {
        return this.parent;
    }
    get plot_model() {
        return this.parent.model;
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.properties.active.change, () => {
            if (this.model.active)
                this.activate();
            else
                this.deactivate();
        });
    }
    // activate is triggered by toolbar ui actions
    activate() { }
    // deactivate is triggered by toolbar ui actions
    deactivate() { }
}
exports.ToolView = ToolView;
ToolView.__name__ = "ToolView";
class Tool extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_Tool() {
        this.internal({
            active: [p.Boolean, false],
        });
    }
    get synthetic_renderers() {
        return [];
    }
    // utility function to return a tool name, modified
    // by the active dimensions. Used by tools that have dimensions
    _get_dim_tooltip(name, dims) {
        switch (dims) {
            case "width": return `${name} (x-axis)`;
            case "height": return `${name} (y-axis)`;
            case "both": return name;
        }
    }
    // utility function to get limits along both dimensions, given
    // optional dimensional constraints
    _get_dim_limits([sx0, sy0], [sx1, sy1], frame, dims) {
        const hr = frame.bbox.h_range;
        let sxlim;
        if (dims == 'width' || dims == 'both') {
            sxlim = [array_1.min([sx0, sx1]), array_1.max([sx0, sx1])];
            sxlim = [array_1.max([sxlim[0], hr.start]), array_1.min([sxlim[1], hr.end])];
        }
        else
            sxlim = [hr.start, hr.end];
        const vr = frame.bbox.v_range;
        let sylim;
        if (dims == 'height' || dims == 'both') {
            sylim = [array_1.min([sy0, sy1]), array_1.max([sy0, sy1])];
            sylim = [array_1.max([sylim[0], vr.start]), array_1.min([sylim[1], vr.end])];
        }
        else
            sylim = [vr.start, vr.end];
        return [sxlim, sylim];
    }
}
exports.Tool = Tool;
Tool.__name__ = "Tool";
Tool.init_Tool();
