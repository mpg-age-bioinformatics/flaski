"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const p = require("../../core/properties");
const signaling_1 = require("../../core/signaling");
const array_1 = require("../../core/util/array");
const object_1 = require("../../core/util/object");
const types_1 = require("../../core/util/types");
const layout_dom_1 = require("../layouts/layout_dom");
const title_1 = require("../annotations/title");
const linear_scale_1 = require("../scales/linear_scale");
const toolbar_1 = require("../tools/toolbar");
const column_data_source_1 = require("../sources/column_data_source");
const glyph_renderer_1 = require("../renderers/glyph_renderer");
const data_range1d_1 = require("../ranges/data_range1d");
const plot_canvas_1 = require("./plot_canvas");
exports.PlotView = plot_canvas_1.PlotView;
class Plot extends layout_dom_1.LayoutDOM {
    constructor(attrs) {
        super(attrs);
    }
    static init_Plot() {
        this.prototype.default_view = plot_canvas_1.PlotView;
        this.mixins(["line:outline_", "fill:background_", "fill:border_"]);
        this.define({
            toolbar: [p.Instance, () => new toolbar_1.Toolbar()],
            toolbar_location: [p.Location, 'right'],
            toolbar_sticky: [p.Boolean, true],
            plot_width: [p.Number, 600],
            plot_height: [p.Number, 600],
            frame_width: [p.Number, null],
            frame_height: [p.Number, null],
            title: [p.Any, () => new title_1.Title({ text: "" })],
            title_location: [p.Location, 'above'],
            above: [p.Array, []],
            below: [p.Array, []],
            left: [p.Array, []],
            right: [p.Array, []],
            center: [p.Array, []],
            renderers: [p.Array, []],
            x_range: [p.Instance, () => new data_range1d_1.DataRange1d()],
            extra_x_ranges: [p.Any, {}],
            y_range: [p.Instance, () => new data_range1d_1.DataRange1d()],
            extra_y_ranges: [p.Any, {}],
            x_scale: [p.Instance, () => new linear_scale_1.LinearScale()],
            y_scale: [p.Instance, () => new linear_scale_1.LinearScale()],
            lod_factor: [p.Number, 10],
            lod_interval: [p.Number, 300],
            lod_threshold: [p.Number, 2000],
            lod_timeout: [p.Number, 500],
            hidpi: [p.Boolean, true],
            output_backend: [p.OutputBackend, "canvas"],
            min_border: [p.Number, 5],
            min_border_top: [p.Number, null],
            min_border_left: [p.Number, null],
            min_border_bottom: [p.Number, null],
            min_border_right: [p.Number, null],
            inner_width: [p.Number],
            inner_height: [p.Number],
            outer_width: [p.Number],
            outer_height: [p.Number],
            match_aspect: [p.Boolean, false],
            aspect_scale: [p.Number, 1],
            reset_policy: [p.ResetPolicy, "standard"],
        });
        this.override({
            outline_line_color: "#e5e5e5",
            border_fill_color: "#ffffff",
            background_fill_color: "#ffffff",
        });
    }
    get width() {
        const width = this.getv("width");
        return width != null ? width : this.plot_width;
    }
    get height() {
        const height = this.getv("height");
        return height != null ? height : this.plot_height;
    }
    _doc_attached() {
        super._doc_attached();
        this._tell_document_about_change('inner_height', null, this.inner_height, {});
        this._tell_document_about_change('inner_width', null, this.inner_width, {});
    }
    initialize() {
        super.initialize();
        this.reset = new signaling_1.Signal0(this, "reset");
        for (const xr of object_1.values(this.extra_x_ranges).concat(this.x_range)) {
            let plots = xr.plots;
            if (types_1.isArray(plots)) {
                plots = plots.concat(this);
                xr.setv({ plots }, { silent: true });
            }
        }
        for (const yr of object_1.values(this.extra_y_ranges).concat(this.y_range)) {
            let plots = yr.plots;
            if (types_1.isArray(plots)) {
                plots = plots.concat(this);
                yr.setv({ plots }, { silent: true });
            }
        }
    }
    add_layout(renderer, side = "center") {
        const side_renderers = this.getv(side);
        side_renderers.push(renderer /* XXX */);
    }
    remove_layout(renderer) {
        const del = (items) => {
            array_1.remove_by(items, (item) => item == renderer);
        };
        del(this.left);
        del(this.right);
        del(this.above);
        del(this.below);
        del(this.center);
    }
    add_renderers(...renderers) {
        this.renderers = this.renderers.concat(renderers);
    }
    add_glyph(glyph, source = new column_data_source_1.ColumnDataSource(), extra_attrs = {}) {
        const attrs = Object.assign(Object.assign({}, extra_attrs), { data_source: source, glyph });
        const renderer = new glyph_renderer_1.GlyphRenderer(attrs);
        this.add_renderers(renderer);
        return renderer;
    }
    add_tools(...tools) {
        this.toolbar.tools = this.toolbar.tools.concat(tools);
    }
    get panels() {
        return this.side_panels.concat(this.center);
    }
    get side_panels() {
        const { above, below, left, right } = this;
        return array_1.concat([above, below, left, right]);
    }
}
exports.Plot = Plot;
Plot.__name__ = "Plot";
Plot.init_Plot();
