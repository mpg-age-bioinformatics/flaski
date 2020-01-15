"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const inspect_tool_1 = require("./inspect_tool");
const tooltip_1 = require("../../annotations/tooltip");
const glyph_renderer_1 = require("../../renderers/glyph_renderer");
const graph_renderer_1 = require("../../renderers/graph_renderer");
const util_1 = require("../util");
const hittest = require("../../../core/hittest");
const templating_1 = require("../../../core/util/templating");
const dom_1 = require("../../../core/dom");
const p = require("../../../core/properties");
const color_1 = require("../../../core/util/color");
const object_1 = require("../../../core/util/object");
const types_1 = require("../../../core/util/types");
const build_views_1 = require("../../../core/build_views");
const icons_1 = require("../../../styles/icons");
const tooltips_1 = require("../../../styles/tooltips");
function _nearest_line_hit(i, geometry, sx, sy, dx, dy) {
    const d1 = { x: dx[i], y: dy[i] };
    const d2 = { x: dx[i + 1], y: dy[i + 1] };
    let dist1;
    let dist2;
    if (geometry.type == "span") {
        if (geometry.direction == "h") {
            dist1 = Math.abs(d1.x - sx);
            dist2 = Math.abs(d2.x - sx);
        }
        else {
            dist1 = Math.abs(d1.y - sy);
            dist2 = Math.abs(d2.y - sy);
        }
    }
    else {
        const s = { x: sx, y: sy };
        dist1 = hittest.dist_2_pts(d1, s);
        dist2 = hittest.dist_2_pts(d2, s);
    }
    if (dist1 < dist2)
        return [[d1.x, d1.y], i];
    else
        return [[d2.x, d2.y], i + 1];
}
exports._nearest_line_hit = _nearest_line_hit;
function _line_hit(xs, ys, ind) {
    return [[xs[ind], ys[ind]], ind];
}
exports._line_hit = _line_hit;
class HoverToolView extends inspect_tool_1.InspectToolView {
    initialize() {
        super.initialize();
        this.ttviews = {};
    }
    remove() {
        build_views_1.remove_views(this.ttviews);
        super.remove();
    }
    connect_signals() {
        super.connect_signals();
        for (const r of this.computed_renderers) {
            if (r instanceof glyph_renderer_1.GlyphRenderer)
                this.connect(r.data_source.inspect, this._update);
            else if (r instanceof graph_renderer_1.GraphRenderer) {
                this.connect(r.node_renderer.data_source.inspect, this._update);
                this.connect(r.edge_renderer.data_source.inspect, this._update);
            }
        }
        // TODO: this.connect(this.plot_model.properties.renderers.change, () => this._computed_renderers = this._ttmodels = null)
        this.connect(this.model.properties.renderers.change, () => this._computed_renderers = this._ttmodels = null);
        this.connect(this.model.properties.names.change, () => this._computed_renderers = this._ttmodels = null);
        this.connect(this.model.properties.tooltips.change, () => this._ttmodels = null);
    }
    _compute_ttmodels() {
        const ttmodels = {};
        const tooltips = this.model.tooltips;
        if (tooltips != null) {
            for (const r of this.computed_renderers) {
                if (r instanceof glyph_renderer_1.GlyphRenderer) {
                    const tooltip = new tooltip_1.Tooltip({
                        custom: types_1.isString(tooltips) || types_1.isFunction(tooltips),
                        attachment: this.model.attachment,
                        show_arrow: this.model.show_arrow,
                    });
                    ttmodels[r.id] = tooltip;
                }
                else if (r instanceof graph_renderer_1.GraphRenderer) {
                    const tooltip = new tooltip_1.Tooltip({
                        custom: types_1.isString(tooltips) || types_1.isFunction(tooltips),
                        attachment: this.model.attachment,
                        show_arrow: this.model.show_arrow,
                    });
                    ttmodels[r.node_renderer.id] = tooltip;
                    ttmodels[r.edge_renderer.id] = tooltip;
                }
            }
        }
        build_views_1.build_views(this.ttviews, object_1.values(ttmodels), { parent: this.plot_view });
        return ttmodels;
    }
    get computed_renderers() {
        if (this._computed_renderers == null) {
            const renderers = this.model.renderers;
            const all_renderers = this.plot_model.renderers;
            const names = this.model.names;
            this._computed_renderers = util_1.compute_renderers(renderers, all_renderers, names);
        }
        return this._computed_renderers;
    }
    get ttmodels() {
        if (this._ttmodels == null)
            this._ttmodels = this._compute_ttmodels();
        return this._ttmodels;
    }
    _clear() {
        this._inspect(Infinity, Infinity);
        for (const rid in this.ttmodels) {
            const tt = this.ttmodels[rid];
            tt.clear();
        }
    }
    _move(ev) {
        if (!this.model.active)
            return;
        const { sx, sy } = ev;
        if (!this.plot_view.frame.bbox.contains(sx, sy))
            this._clear();
        else
            this._inspect(sx, sy);
    }
    _move_exit() {
        this._clear();
    }
    _inspect(sx, sy) {
        let geometry;
        if (this.model.mode == 'mouse')
            geometry = { type: 'point', sx, sy };
        else {
            const direction = this.model.mode == 'vline' ? 'h' : 'v';
            geometry = { type: 'span', direction, sx, sy };
        }
        for (const r of this.computed_renderers) {
            const sm = r.get_selection_manager();
            sm.inspect(this.plot_view.renderer_views[r.id], geometry);
        }
        if (this.model.callback != null)
            this._emit_callback(geometry);
    }
    _update([renderer_view, { geometry }]) {
        if (!this.model.active)
            return;
        if (!(renderer_view instanceof glyph_renderer_1.GlyphRendererView || renderer_view instanceof graph_renderer_1.GraphRendererView))
            return;
        const { model: renderer } = renderer_view;
        const tooltip = this.ttmodels[renderer.id];
        if (tooltip == null)
            return;
        tooltip.clear();
        const selection_manager = renderer.get_selection_manager();
        let indices = selection_manager.inspectors[renderer.id];
        if (renderer instanceof glyph_renderer_1.GlyphRenderer)
            indices = renderer.view.convert_selection_to_subset(indices);
        if (indices.is_empty())
            return;
        const ds = selection_manager.source;
        const { frame } = this.plot_view;
        const { sx, sy } = geometry;
        const xscale = frame.xscales[renderer.x_range_name];
        const yscale = frame.yscales[renderer.y_range_name];
        const x = xscale.invert(sx);
        const y = yscale.invert(sy);
        const glyph = renderer_view.glyph; // XXX
        for (const i of indices.line_indices) {
            let data_x = glyph._x[i + 1];
            let data_y = glyph._y[i + 1];
            let ii = i;
            let rx;
            let ry;
            switch (this.model.line_policy) {
                case "interp": { // and renderer.get_interpolation_hit?
                    [data_x, data_y] = glyph.get_interpolation_hit(i, geometry);
                    rx = xscale.compute(data_x);
                    ry = yscale.compute(data_y);
                    break;
                }
                case "prev": {
                    [[rx, ry], ii] = _line_hit(glyph.sx, glyph.sy, i);
                    break;
                }
                case "next": {
                    [[rx, ry], ii] = _line_hit(glyph.sx, glyph.sy, i + 1);
                    break;
                }
                case "nearest": {
                    [[rx, ry], ii] = _nearest_line_hit(i, geometry, sx, sy, glyph.sx, glyph.sy);
                    data_x = glyph._x[ii];
                    data_y = glyph._y[ii];
                    break;
                }
                default: {
                    [rx, ry] = [sx, sy];
                }
            }
            const vars = {
                index: ii,
                x, y, sx, sy, data_x, data_y, rx, ry,
                indices: indices.line_indices,
                name: renderer_view.model.name,
            };
            tooltip.add(rx, ry, this._render_tooltips(ds, ii, vars));
        }
        for (const struct of indices.image_indices) {
            const vars = { index: struct.index, x, y, sx, sy };
            const rendered = this._render_tooltips(ds, struct, vars);
            tooltip.add(sx, sy, rendered);
        }
        for (const i of indices.indices) {
            // multiglyphs set additional indices, e.g. multiline_indices for different tooltips
            if (!object_1.isEmpty(indices.multiline_indices)) {
                for (const j of indices.multiline_indices[i.toString()]) {
                    let data_x = glyph._xs[i][j];
                    let data_y = glyph._ys[i][j];
                    let jj = j;
                    let rx;
                    let ry;
                    switch (this.model.line_policy) {
                        case "interp": { // and renderer.get_interpolation_hit?
                            [data_x, data_y] = glyph.get_interpolation_hit(i, j, geometry);
                            rx = xscale.compute(data_x);
                            ry = yscale.compute(data_y);
                            break;
                        }
                        case "prev": {
                            [[rx, ry], jj] = _line_hit(glyph.sxs[i], glyph.sys[i], j);
                            break;
                        }
                        case "next": {
                            [[rx, ry], jj] = _line_hit(glyph.sxs[i], glyph.sys[i], j + 1);
                            break;
                        }
                        case "nearest": {
                            [[rx, ry], jj] = _nearest_line_hit(j, geometry, sx, sy, glyph.sxs[i], glyph.sys[i]);
                            data_x = glyph._xs[i][jj];
                            data_y = glyph._ys[i][jj];
                            break;
                        }
                        default:
                            throw new Error("should't have happened");
                    }
                    let index;
                    if (renderer instanceof glyph_renderer_1.GlyphRenderer)
                        index = renderer.view.convert_indices_from_subset([i])[0];
                    else
                        index = i;
                    const vars = {
                        index, x, y, sx, sy, data_x, data_y,
                        segment_index: jj,
                        indices: indices.multiline_indices,
                        name: renderer_view.model.name,
                    };
                    tooltip.add(rx, ry, this._render_tooltips(ds, index, vars));
                }
            }
            else {
                // handle non-multiglyphs
                const data_x = glyph._x != null ? glyph._x[i] : undefined;
                const data_y = glyph._y != null ? glyph._y[i] : undefined;
                let rx;
                let ry;
                if (this.model.point_policy == 'snap_to_data') { // and renderer.glyph.sx? and renderer.glyph.sy?
                    // Pass in our screen position so we can determine which patch we're
                    // over if there are discontinuous patches.
                    let pt = glyph.get_anchor_point(this.model.anchor, i, [sx, sy]);
                    if (pt == null)
                        pt = glyph.get_anchor_point("center", i, [sx, sy]);
                    rx = pt.x;
                    ry = pt.y;
                }
                else
                    [rx, ry] = [sx, sy];
                let index;
                if (renderer instanceof glyph_renderer_1.GlyphRenderer)
                    index = renderer.view.convert_indices_from_subset([i])[0];
                else
                    index = i;
                const vars = {
                    index, x, y, sx, sy, data_x, data_y,
                    indices: indices.indices,
                    name: renderer_view.model.name,
                };
                tooltip.add(rx, ry, this._render_tooltips(ds, index, vars));
            }
        }
    }
    _emit_callback(geometry) {
        for (const r of this.computed_renderers) {
            const index = r.data_source.inspected;
            const { frame } = this.plot_view;
            const xscale = frame.xscales[r.x_range_name];
            const yscale = frame.yscales[r.y_range_name];
            const x = xscale.invert(geometry.sx);
            const y = yscale.invert(geometry.sy);
            const g = Object.assign({ x, y }, geometry);
            this.model.callback.execute(this.model, { index, geometry: g, renderer: r });
        }
    }
    _render_tooltips(ds, i, vars) {
        const tooltips = this.model.tooltips;
        if (types_1.isString(tooltips)) {
            const el = dom_1.div();
            el.innerHTML = templating_1.replace_placeholders(tooltips, ds, i, this.model.formatters, vars);
            return el;
        }
        else if (types_1.isFunction(tooltips)) {
            return tooltips(ds, vars);
        }
        else {
            const rows = dom_1.div({ style: { display: "table", borderSpacing: "2px" } });
            for (const [label, value] of tooltips) {
                const row = dom_1.div({ style: { display: "table-row" } });
                rows.appendChild(row);
                let cell;
                cell = dom_1.div({ style: { display: "table-cell" }, class: tooltips_1.bk_tooltip_row_label }, label.length != 0 ? `${label}: ` : "");
                row.appendChild(cell);
                cell = dom_1.div({ style: { display: "table-cell" }, class: tooltips_1.bk_tooltip_row_value });
                row.appendChild(cell);
                if (value.indexOf("$color") >= 0) {
                    const [, opts = "", colname] = value.match(/\$color(\[.*\])?:(\w*)/); // XXX!
                    const column = ds.get_column(colname); // XXX: change to columnar ds
                    if (column == null) {
                        const el = dom_1.span({}, `${colname} unknown`);
                        cell.appendChild(el);
                        continue;
                    }
                    const hex = opts.indexOf("hex") >= 0;
                    const swatch = opts.indexOf("swatch") >= 0;
                    let color = types_1.isNumber(i) ? column[i] : null;
                    if (color == null) {
                        const el = dom_1.span({}, "(null)");
                        cell.appendChild(el);
                        continue;
                    }
                    if (hex)
                        color = color_1.color2hex(color);
                    let el = dom_1.span({}, color);
                    cell.appendChild(el);
                    if (swatch) {
                        el = dom_1.span({ class: tooltips_1.bk_tooltip_color_block, style: { backgroundColor: color } }, " ");
                        cell.appendChild(el);
                    }
                }
                else {
                    const el = dom_1.span();
                    el.innerHTML = templating_1.replace_placeholders(value.replace("$~", "$data_"), ds, i, this.model.formatters, vars);
                    cell.appendChild(el);
                }
            }
            return rows;
        }
    }
}
exports.HoverToolView = HoverToolView;
HoverToolView.__name__ = "HoverToolView";
class HoverTool extends inspect_tool_1.InspectTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Hover";
        this.icon = icons_1.bk_tool_icon_hover;
    }
    static init_HoverTool() {
        this.prototype.default_view = HoverToolView;
        this.define({
            tooltips: [p.Any, [
                    ["index", "$index"],
                    ["data (x, y)", "($x, $y)"],
                    ["screen (x, y)", "($sx, $sy)"],
                ]],
            formatters: [p.Any, {}],
            renderers: [p.Any, 'auto'],
            names: [p.Array, []],
            mode: [p.HoverMode, 'mouse'],
            point_policy: [p.PointPolicy, 'snap_to_data'],
            line_policy: [p.LinePolicy, 'nearest'],
            show_arrow: [p.Boolean, true],
            anchor: [p.Anchor, 'center'],
            attachment: [p.TooltipAttachment, 'horizontal'],
            callback: [p.Any],
        });
    }
}
exports.HoverTool = HoverTool;
HoverTool.__name__ = "HoverTool";
HoverTool.init_HoverTool();
