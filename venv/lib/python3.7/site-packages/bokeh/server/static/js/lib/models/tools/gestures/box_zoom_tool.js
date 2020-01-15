"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const gesture_tool_1 = require("./gesture_tool");
const box_annotation_1 = require("../../annotations/box_annotation");
const p = require("../../../core/properties");
const icons_1 = require("../../../styles/icons");
class BoxZoomToolView extends gesture_tool_1.GestureToolView {
    _match_aspect(base_point, curpoint, frame) {
        // aspect ratio of plot frame
        const a = frame.bbox.aspect;
        const hend = frame.bbox.h_range.end;
        const hstart = frame.bbox.h_range.start;
        const vend = frame.bbox.v_range.end;
        const vstart = frame.bbox.v_range.start;
        // current aspect of cursor-defined box
        let vw = Math.abs(base_point[0] - curpoint[0]);
        let vh = Math.abs(base_point[1] - curpoint[1]);
        const va = vh == 0 ? 0 : vw / vh;
        const [xmod] = va >= a ? [1, va / a] : [a / va, 1];
        // OK the code blocks below merit some explanation. They do:
        //
        // compute left/right, pin to frame if necessary
        // compute top/bottom (based on new left/right), pin to frame if necessary
        // recompute left/right (based on top/bottom), in case top/bottom were pinned
        // base_point[0] is left
        let left;
        let right;
        if (base_point[0] <= curpoint[0]) {
            left = base_point[0];
            right = base_point[0] + vw * xmod;
            if (right > hend)
                right = hend;
            // base_point[0] is right
        }
        else {
            right = base_point[0];
            left = base_point[0] - vw * xmod;
            if (left < hstart)
                left = hstart;
        }
        vw = Math.abs(right - left);
        // base_point[1] is bottom
        let top;
        let bottom;
        if (base_point[1] <= curpoint[1]) {
            bottom = base_point[1];
            top = base_point[1] + vw / a;
            if (top > vend)
                top = vend;
            // base_point[1] is top
        }
        else {
            top = base_point[1];
            bottom = base_point[1] - vw / a;
            if (bottom < vstart)
                bottom = vstart;
        }
        vh = Math.abs(top - bottom);
        // base_point[0] is left
        if (base_point[0] <= curpoint[0])
            right = base_point[0] + a * vh;
        // base_point[0] is right
        else
            left = base_point[0] - a * vh;
        return [[left, right], [bottom, top]];
    }
    _compute_limits(curpoint) {
        const frame = this.plot_view.frame;
        const dims = this.model.dimensions;
        let base_point = this._base_point;
        if (this.model.origin == "center") {
            const [cx, cy] = base_point;
            const [dx, dy] = curpoint;
            base_point = [cx - (dx - cx), cy - (dy - cy)];
        }
        let sx;
        let sy;
        if (this.model.match_aspect && dims == 'both')
            [sx, sy] = this._match_aspect(base_point, curpoint, frame);
        else
            [sx, sy] = this.model._get_dim_limits(base_point, curpoint, frame, dims);
        return [sx, sy];
    }
    _pan_start(ev) {
        this._base_point = [ev.sx, ev.sy];
    }
    _pan(ev) {
        const curpoint = [ev.sx, ev.sy];
        const [sx, sy] = this._compute_limits(curpoint);
        this.model.overlay.update({ left: sx[0], right: sx[1], top: sy[0], bottom: sy[1] });
    }
    _pan_end(ev) {
        const curpoint = [ev.sx, ev.sy];
        const [sx, sy] = this._compute_limits(curpoint);
        this._update(sx, sy);
        this.model.overlay.update({ left: null, right: null, top: null, bottom: null });
        this._base_point = null;
    }
    _update([sx0, sx1], [sy0, sy1]) {
        // If the viewing window is too small, no-op: it is likely that the user did
        // not intend to make this box zoom and instead was trying to cancel out of the
        // zoom, a la matplotlib's ToolZoom. Like matplotlib, set the threshold at 5 pixels.
        if (Math.abs(sx1 - sx0) <= 5 || Math.abs(sy1 - sy0) <= 5)
            return;
        const { xscales, yscales } = this.plot_view.frame;
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
        const zoom_info = { xrs, yrs };
        this.plot_view.push_state('box_zoom', { range: zoom_info });
        this.plot_view.update_range(zoom_info);
    }
}
exports.BoxZoomToolView = BoxZoomToolView;
BoxZoomToolView.__name__ = "BoxZoomToolView";
const DEFAULT_BOX_OVERLAY = () => {
    return new box_annotation_1.BoxAnnotation({
        level: "overlay",
        render_mode: "css",
        top_units: "screen",
        left_units: "screen",
        bottom_units: "screen",
        right_units: "screen",
        fill_color: { value: "lightgrey" },
        fill_alpha: { value: 0.5 },
        line_color: { value: "black" },
        line_alpha: { value: 1.0 },
        line_width: { value: 2 },
        line_dash: { value: [4, 4] },
    });
};
class BoxZoomTool extends gesture_tool_1.GestureTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Box Zoom";
        this.icon = icons_1.bk_tool_icon_box_zoom;
        this.event_type = "pan";
        this.default_order = 20;
    }
    static init_BoxZoomTool() {
        this.prototype.default_view = BoxZoomToolView;
        this.define({
            dimensions: [p.Dimensions, "both"],
            overlay: [p.Instance, DEFAULT_BOX_OVERLAY],
            match_aspect: [p.Boolean, false],
            origin: [p.BoxOrigin, "corner"],
        });
    }
    get tooltip() {
        return this._get_dim_tooltip(this.tool_name, this.dimensions);
    }
}
exports.BoxZoomTool = BoxZoomTool;
BoxZoomTool.__name__ = "BoxZoomTool";
BoxZoomTool.init_BoxZoomTool();
