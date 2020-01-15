"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const action_tool_1 = require("./action_tool");
const zoom_1 = require("../../../core/util/zoom");
const p = require("../../../core/properties");
const icons_1 = require("../../../styles/icons");
class ZoomInToolView extends action_tool_1.ActionToolView {
    doit() {
        const frame = this.plot_view.frame;
        const dims = this.model.dimensions;
        // restrict to axis configured in tool's dimensions property
        const h_axis = dims == 'width' || dims == 'both';
        const v_axis = dims == 'height' || dims == 'both';
        const zoom_info = zoom_1.scale_range(frame, this.model.factor, h_axis, v_axis);
        this.plot_view.push_state('zoom_out', { range: zoom_info });
        this.plot_view.update_range(zoom_info, false, true);
        if (this.model.document)
            this.model.document.interactive_start(this.plot_model);
    }
}
exports.ZoomInToolView = ZoomInToolView;
ZoomInToolView.__name__ = "ZoomInToolView";
class ZoomInTool extends action_tool_1.ActionTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Zoom In";
        this.icon = icons_1.bk_tool_icon_zoom_in;
    }
    static init_ZoomInTool() {
        this.prototype.default_view = ZoomInToolView;
        this.define({
            factor: [p.Percent, 0.1],
            dimensions: [p.Dimensions, "both"],
        });
    }
    get tooltip() {
        return this._get_dim_tooltip(this.tool_name, this.dimensions);
    }
}
exports.ZoomInTool = ZoomInTool;
ZoomInTool.__name__ = "ZoomInTool";
ZoomInTool.init_ZoomInTool();
