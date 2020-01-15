"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const gesture_tool_1 = require("./gesture_tool");
const p = require("../../../core/properties");
const icons_1 = require("../../../styles/icons");
class WheelPanToolView extends gesture_tool_1.GestureToolView {
    _scroll(ev) {
        let factor = this.model.speed * ev.delta;
        // clamp the magnitude of factor, if it is > 1 bad things happen
        if (factor > 0.9)
            factor = 0.9;
        else if (factor < -0.9)
            factor = -0.9;
        this._update_ranges(factor);
    }
    _update_ranges(factor) {
        const { frame } = this.plot_view;
        const hr = frame.bbox.h_range;
        const vr = frame.bbox.v_range;
        const [sx_low, sx_high] = [hr.start, hr.end];
        const [sy_low, sy_high] = [vr.start, vr.end];
        let sx0;
        let sx1;
        let sy0;
        let sy1;
        switch (this.model.dimension) {
            case "height": {
                const sy_range = Math.abs(sy_high - sy_low);
                sx0 = sx_low;
                sx1 = sx_high;
                sy0 = sy_low - sy_range * factor;
                sy1 = sy_high - sy_range * factor;
                break;
            }
            case "width": {
                const sx_range = Math.abs(sx_high - sx_low);
                sx0 = sx_low - sx_range * factor;
                sx1 = sx_high - sx_range * factor;
                sy0 = sy_low;
                sy1 = sy_high;
                break;
            }
            default:
                throw new Error("this shouldn't have happened");
        }
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
        // OK this sucks we can't set factor independently in each direction. It is used
        // for GMap plots, and GMap plots always preserve aspect, so effective the value
        // of 'dimensions' is ignored.
        const pan_info = { xrs, yrs, factor };
        this.plot_view.push_state('wheel_pan', { range: pan_info });
        this.plot_view.update_range(pan_info, false, true);
        if (this.model.document != null)
            this.model.document.interactive_start(this.plot_model);
    }
}
exports.WheelPanToolView = WheelPanToolView;
WheelPanToolView.__name__ = "WheelPanToolView";
class WheelPanTool extends gesture_tool_1.GestureTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Wheel Pan";
        this.icon = icons_1.bk_tool_icon_wheel_pan;
        this.event_type = "scroll";
        this.default_order = 12;
    }
    static init_WheelPanTool() {
        this.prototype.default_view = WheelPanToolView;
        this.define({
            dimension: [p.Dimension, "width"],
        });
        this.internal({
            speed: [p.Number, 1 / 1000],
        });
    }
    get tooltip() {
        return this._get_dim_tooltip(this.tool_name, this.dimension);
    }
}
exports.WheelPanTool = WheelPanTool;
WheelPanTool.__name__ = "WheelPanTool";
WheelPanTool.init_WheelPanTool();
