"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const inspect_tool_1 = require("./inspect_tool");
const span_1 = require("../../annotations/span");
const p = require("../../../core/properties");
const object_1 = require("../../../core/util/object");
const icons_1 = require("../../../styles/icons");
class CrosshairToolView extends inspect_tool_1.InspectToolView {
    _move(ev) {
        if (!this.model.active)
            return;
        const { sx, sy } = ev;
        if (!this.plot_view.frame.bbox.contains(sx, sy))
            this._update_spans(null, null);
        else
            this._update_spans(sx, sy);
    }
    _move_exit(_e) {
        this._update_spans(null, null);
    }
    _update_spans(x, y) {
        const dims = this.model.dimensions;
        if (dims == "width" || dims == "both")
            this.model.spans.width.computed_location = y;
        if (dims == "height" || dims == "both")
            this.model.spans.height.computed_location = x;
    }
}
exports.CrosshairToolView = CrosshairToolView;
CrosshairToolView.__name__ = "CrosshairToolView";
class CrosshairTool extends inspect_tool_1.InspectTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Crosshair";
        this.icon = icons_1.bk_tool_icon_crosshair;
    }
    static init_CrosshairTool() {
        this.prototype.default_view = CrosshairToolView;
        this.define({
            dimensions: [p.Dimensions, "both"],
            line_color: [p.Color, 'black'],
            line_width: [p.Number, 1],
            line_alpha: [p.Number, 1.0],
        });
        this.internal({
            location_units: [p.SpatialUnits, "screen"],
            render_mode: [p.RenderMode, "css"],
            spans: [p.Any],
        });
    }
    get tooltip() {
        return this._get_dim_tooltip("Crosshair", this.dimensions);
    }
    get synthetic_renderers() {
        return object_1.values(this.spans);
    }
    initialize() {
        super.initialize();
        this.spans = {
            width: new span_1.Span({
                for_hover: true,
                dimension: "width",
                render_mode: this.render_mode,
                location_units: this.location_units,
                line_color: this.line_color,
                line_width: this.line_width,
                line_alpha: this.line_alpha,
            }),
            height: new span_1.Span({
                for_hover: true,
                dimension: "height",
                render_mode: this.render_mode,
                location_units: this.location_units,
                line_color: this.line_color,
                line_width: this.line_width,
                line_alpha: this.line_alpha,
            }),
        };
    }
}
exports.CrosshairTool = CrosshairTool;
CrosshairTool.__name__ = "CrosshairTool";
CrosshairTool.init_CrosshairTool();
