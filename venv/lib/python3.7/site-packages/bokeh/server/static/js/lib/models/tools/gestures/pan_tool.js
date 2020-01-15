"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const gesture_tool_1 = require("./gesture_tool");
const p = require("../../../core/properties");
const icons_1 = require("../../../styles/icons");
class PanToolView extends gesture_tool_1.GestureToolView {
    _pan_start(ev) {
        this.last_dx = 0;
        this.last_dy = 0;
        const { sx, sy } = ev;
        const bbox = this.plot_view.frame.bbox;
        if (!bbox.contains(sx, sy)) {
            const hr = bbox.h_range;
            const vr = bbox.v_range;
            if (sx < hr.start || sx > hr.end)
                this.v_axis_only = true;
            if (sy < vr.start || sy > vr.end)
                this.h_axis_only = true;
        }
        if (this.model.document != null)
            this.model.document.interactive_start(this.plot_model);
    }
    _pan(ev) {
        this._update(ev.deltaX, ev.deltaY);
        if (this.model.document != null)
            this.model.document.interactive_start(this.plot_model);
    }
    _pan_end(_e) {
        this.h_axis_only = false;
        this.v_axis_only = false;
        if (this.pan_info != null)
            this.plot_view.push_state('pan', { range: this.pan_info });
    }
    _update(dx, dy) {
        const frame = this.plot_view.frame;
        const new_dx = dx - this.last_dx;
        const new_dy = dy - this.last_dy;
        const hr = frame.bbox.h_range;
        const sx_low = hr.start - new_dx;
        const sx_high = hr.end - new_dx;
        const vr = frame.bbox.v_range;
        const sy_low = vr.start - new_dy;
        const sy_high = vr.end - new_dy;
        const dims = this.model.dimensions;
        let sx0;
        let sx1;
        let sdx;
        if ((dims == 'width' || dims == 'both') && !this.v_axis_only) {
            sx0 = sx_low;
            sx1 = sx_high;
            sdx = -new_dx;
        }
        else {
            sx0 = hr.start;
            sx1 = hr.end;
            sdx = 0;
        }
        let sy0;
        let sy1;
        let sdy;
        if ((dims == 'height' || dims == 'both') && !this.h_axis_only) {
            sy0 = sy_low;
            sy1 = sy_high;
            sdy = -new_dy;
        }
        else {
            sy0 = vr.start;
            sy1 = vr.end;
            sdy = 0;
        }
        this.last_dx = dx;
        this.last_dy = dy;
        const { xscales, yscales } = frame;
        const xrs = {};
        for (const name in xscales) {
            const scale = xscales[name];
            const [start, end] = scale.r_invert(sx0, sx1);
            xrs[name] = { start, end };
        }
        const yrs = {};
        for (const name in yscales) {
            const scale = yscales[name];
            const [start, end] = scale.r_invert(sy0, sy1);
            yrs[name] = { start, end };
        }
        this.pan_info = { xrs, yrs, sdx, sdy };
        this.plot_view.update_range(this.pan_info, true);
    }
}
exports.PanToolView = PanToolView;
PanToolView.__name__ = "PanToolView";
class PanTool extends gesture_tool_1.GestureTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Pan";
        this.event_type = "pan";
        this.default_order = 10;
    }
    static init_PanTool() {
        this.prototype.default_view = PanToolView;
        this.define({
            dimensions: [p.Dimensions, "both"],
        });
    }
    get tooltip() {
        return this._get_dim_tooltip("Pan", this.dimensions);
    }
    get icon() {
        switch (this.dimensions) {
            case "both": return icons_1.bk_tool_icon_pan;
            case "width": return icons_1.bk_tool_icon_xpan;
            case "height": return icons_1.bk_tool_icon_ypan;
        }
    }
}
exports.PanTool = PanTool;
PanTool.__name__ = "PanTool";
PanTool.init_PanTool();
