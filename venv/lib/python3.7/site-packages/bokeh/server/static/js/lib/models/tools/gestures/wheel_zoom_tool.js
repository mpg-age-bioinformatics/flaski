"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const gesture_tool_1 = require("./gesture_tool");
const zoom_1 = require("../../../core/util/zoom");
const p = require("../../../core/properties");
const compat_1 = require("../../../core/util/compat");
const icons_1 = require("../../../styles/icons");
class WheelZoomToolView extends gesture_tool_1.GestureToolView {
    _pinch(ev) {
        // TODO (bev) this can probably be done much better
        const { sx, sy, scale } = ev;
        let delta;
        if (scale >= 1)
            delta = (scale - 1) * 20.0;
        else
            delta = -20.0 / scale;
        this._scroll({ type: "wheel", sx, sy, delta });
    }
    _scroll(ev) {
        const { frame } = this.plot_view;
        const hr = frame.bbox.h_range;
        const vr = frame.bbox.v_range;
        const { sx, sy } = ev;
        const dims = this.model.dimensions;
        // restrict to axis configured in tool's dimensions property and if
        // zoom origin is inside of frame range/domain
        const h_axis = (dims == 'width' || dims == 'both') && hr.start < sx && sx < hr.end;
        const v_axis = (dims == 'height' || dims == 'both') && vr.start < sy && sy < vr.end;
        if ((!h_axis || !v_axis) && !this.model.zoom_on_axis) {
            return;
        }
        const factor = this.model.speed * ev.delta;
        const zoom_info = zoom_1.scale_range(frame, factor, h_axis, v_axis, { x: sx, y: sy });
        this.plot_view.push_state('wheel_zoom', { range: zoom_info });
        this.plot_view.update_range(zoom_info, false, true, this.model.maintain_focus);
        if (this.model.document != null)
            this.model.document.interactive_start(this.plot_model);
    }
}
exports.WheelZoomToolView = WheelZoomToolView;
WheelZoomToolView.__name__ = "WheelZoomToolView";
class WheelZoomTool extends gesture_tool_1.GestureTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Wheel Zoom";
        this.icon = icons_1.bk_tool_icon_wheel_zoom;
        this.event_type = compat_1.is_mobile ? "pinch" : "scroll";
        this.default_order = 10;
    }
    static init_WheelZoomTool() {
        this.prototype.default_view = WheelZoomToolView;
        this.define({
            dimensions: [p.Dimensions, "both"],
            maintain_focus: [p.Boolean, true],
            zoom_on_axis: [p.Boolean, true],
            speed: [p.Number, 1 / 600],
        });
    }
    get tooltip() {
        return this._get_dim_tooltip(this.tool_name, this.dimensions);
    }
}
exports.WheelZoomTool = WheelZoomTool;
WheelZoomTool.__name__ = "WheelZoomTool";
WheelZoomTool.init_WheelZoomTool();
