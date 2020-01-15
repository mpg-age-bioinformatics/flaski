"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const action_tool_1 = require("./action_tool");
const zoom_1 = require("../../../core/util/zoom");
const p = require("../../../core/properties");
const icons_1 = require("../../../styles/icons");
class ZoomOutToolView extends action_tool_1.ActionToolView {
    doit() {
        const frame = this.plot_view.frame;
        const dims = this.model.dimensions;
        // restrict to axis configured in tool's dimensions property
        const h_axis = dims == 'width' || dims == 'both';
        const v_axis = dims == 'height' || dims == 'both';
        // zooming out requires a negative factor to scale_range
        const zoom_info = zoom_1.scale_range(frame, -this.model.factor, h_axis, v_axis);
        this.plot_view.push_state('zoom_out', { range: zoom_info });
        this.plot_view.update_range(zoom_info, false, true);
        if (this.model.document)
            this.model.document.interactive_start(this.plot_model);
    }
}
exports.ZoomOutToolView = ZoomOutToolView;
ZoomOutToolView.__name__ = "ZoomOutToolView";
class ZoomOutTool extends action_tool_1.ActionTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Zoom Out";
        this.icon = icons_1.bk_tool_icon_zoom_out;
    }
    static init_ZoomOutTool() {
        this.prototype.default_view = ZoomOutToolView;
        this.define({
            factor: [p.Percent, 0.1],
            dimensions: [p.Dimensions, "both"],
        });
    }
    get tooltip() {
        return this._get_dim_tooltip(this.tool_name, this.dimensions);
    }
}
exports.ZoomOutTool = ZoomOutTool;
ZoomOutTool.__name__ = "ZoomOutTool";
ZoomOutTool.init_ZoomOutTool();
