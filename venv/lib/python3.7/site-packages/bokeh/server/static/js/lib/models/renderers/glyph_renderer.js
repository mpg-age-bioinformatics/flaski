"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const data_renderer_1 = require("./data_renderer");
const line_1 = require("../glyphs/line");
const patch_1 = require("../glyphs/patch");
const harea_1 = require("../glyphs/harea");
const varea_1 = require("../glyphs/varea");
const cds_view_1 = require("../sources/cds_view");
const logging_1 = require("../../core/logging");
const p = require("../../core/properties");
const arrayable_1 = require("../../core/util/arrayable");
const array_1 = require("../../core/util/array");
const object_1 = require("../../core/util/object");
const factor_range_1 = require("../ranges/factor_range");
const selection_defaults = {
    fill: {},
    line: {},
};
const decimated_defaults = {
    fill: { fill_alpha: 0.3, fill_color: "grey" },
    line: { line_alpha: 0.3, line_color: "grey" },
};
const nonselection_defaults = {
    fill: { fill_alpha: 0.2 },
    line: {},
};
class GlyphRendererView extends data_renderer_1.DataRendererView {
    initialize() {
        super.initialize();
        const base_glyph = this.model.glyph;
        const has_fill = array_1.includes(base_glyph.mixins, "fill");
        const has_line = array_1.includes(base_glyph.mixins, "line");
        const glyph_attrs = object_1.clone(base_glyph.attributes);
        delete glyph_attrs.id;
        function mk_glyph(defaults) {
            const attrs = object_1.clone(glyph_attrs);
            if (has_fill)
                object_1.extend(attrs, defaults.fill);
            if (has_line)
                object_1.extend(attrs, defaults.line);
            return new base_glyph.constructor(attrs);
        }
        this.glyph = this.build_glyph_view(base_glyph);
        let { selection_glyph } = this.model;
        if (selection_glyph == null)
            selection_glyph = mk_glyph({ fill: {}, line: {} });
        else if (selection_glyph === "auto")
            selection_glyph = mk_glyph(selection_defaults);
        this.selection_glyph = this.build_glyph_view(selection_glyph);
        let { nonselection_glyph } = this.model;
        if ((nonselection_glyph == null))
            nonselection_glyph = mk_glyph({ fill: {}, line: {} });
        else if (nonselection_glyph === "auto")
            nonselection_glyph = mk_glyph(nonselection_defaults);
        this.nonselection_glyph = this.build_glyph_view(nonselection_glyph);
        const { hover_glyph } = this.model;
        if (hover_glyph != null)
            this.hover_glyph = this.build_glyph_view(hover_glyph);
        const { muted_glyph } = this.model;
        if (muted_glyph != null)
            this.muted_glyph = this.build_glyph_view(muted_glyph);
        const decimated_glyph = mk_glyph(decimated_defaults);
        this.decimated_glyph = this.build_glyph_view(decimated_glyph);
        this.xscale = this.plot_view.frame.xscales[this.model.x_range_name];
        this.yscale = this.plot_view.frame.yscales[this.model.y_range_name];
        this.set_data(false);
    }
    build_glyph_view(model) {
        return new model.default_view({ model, parent: this }); // XXX
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.change, () => this.request_render());
        this.connect(this.model.glyph.change, () => this.set_data());
        this.connect(this.model.data_source.change, () => this.set_data());
        this.connect(this.model.data_source.streaming, () => this.set_data());
        this.connect(this.model.data_source.patching, (indices /* XXX: WHY? */) => this.set_data(true, indices));
        this.connect(this.model.data_source.selected.change, () => this.request_render());
        this.connect(this.model.data_source._select, () => this.request_render());
        if (this.hover_glyph != null)
            this.connect(this.model.data_source.inspect, () => this.request_render());
        this.connect(this.model.properties.view.change, () => this.set_data());
        this.connect(this.model.view.change, () => this.set_data());
        this.connect(this.model.properties.visible.change, () => this.plot_view.update_dataranges());
        const { x_ranges, y_ranges } = this.plot_view.frame;
        for (const name in x_ranges) {
            const rng = x_ranges[name];
            if (rng instanceof factor_range_1.FactorRange)
                this.connect(rng.change, () => this.set_data());
        }
        for (const name in y_ranges) {
            const rng = y_ranges[name];
            if (rng instanceof factor_range_1.FactorRange)
                this.connect(rng.change, () => this.set_data());
        }
        this.connect(this.model.glyph.transformchange, () => this.set_data());
    }
    have_selection_glyphs() {
        return this.selection_glyph != null && this.nonselection_glyph != null;
    }
    // in case of partial updates like patching, the list of indices that actually
    // changed may be passed as the "indices" parameter to afford any optional optimizations
    set_data(request_render = true, indices = null) {
        const t0 = Date.now();
        const source = this.model.data_source;
        this.all_indices = this.model.view.indices;
        // TODO (bev) this is a bit clunky, need to make sure glyphs use the correct ranges when they call
        // mapping functions on the base Renderer class
        this.glyph.model.setv({ x_range_name: this.model.x_range_name,
            y_range_name: this.model.y_range_name }, { silent: true });
        this.glyph.set_data(source, this.all_indices, indices);
        this.glyph.set_visuals(source);
        this.decimated_glyph.set_visuals(source);
        if (this.have_selection_glyphs()) {
            this.selection_glyph.set_visuals(source);
            this.nonselection_glyph.set_visuals(source);
        }
        if (this.hover_glyph != null)
            this.hover_glyph.set_visuals(source);
        if (this.muted_glyph != null)
            this.muted_glyph.set_visuals(source);
        const { lod_factor } = this.plot_model;
        this.decimated = [];
        for (let i = 0, end = Math.floor(this.all_indices.length / lod_factor); i < end; i++) {
            this.decimated.push(i * lod_factor);
        }
        const dt = Date.now() - t0;
        logging_1.logger.debug(`${this.glyph.model.type} GlyphRenderer (${this.model.id}): set_data finished in ${dt}ms`);
        this.set_data_timestamp = Date.now();
        if (request_render)
            this.request_render();
    }
    get has_webgl() {
        return this.glyph.glglyph != null;
    }
    render() {
        if (!this.model.visible)
            return;
        const t0 = Date.now();
        const glsupport = this.has_webgl;
        this.glyph.map_data();
        const dtmap = Date.now() - t0;
        const tmask = Date.now();
        // all_indices is in full data space, indices is converted to subset space
        // either by mask_data (that uses the spatial index) or manually
        let indices = this.glyph.mask_data(this.all_indices);
        if (indices.length === this.all_indices.length) {
            indices = array_1.range(0, this.all_indices.length);
        }
        const dtmask = Date.now() - tmask;
        const { ctx } = this.plot_view.canvas_view;
        ctx.save();
        // selected is in full set space
        const { selected } = this.model.data_source;
        let selected_full_indices;
        if (!selected || selected.is_empty())
            selected_full_indices = [];
        else {
            if (this.glyph instanceof line_1.LineView && selected.selected_glyph === this.glyph.model)
                selected_full_indices = this.model.view.convert_indices_from_subset(indices);
            else
                selected_full_indices = selected.indices;
        }
        // inspected is in full set space
        const { inspected } = this.model.data_source;
        const inspected_full_indices = new Set((() => {
            if (!inspected || inspected.is_empty())
                return [];
            else {
                if (inspected['0d'].glyph)
                    return this.model.view.convert_indices_from_subset(indices);
                else if (inspected['1d'].indices.length > 0)
                    return inspected['1d'].indices;
                else
                    return arrayable_1.map(Object.keys(inspected["2d"].indices), (i) => parseInt(i));
            }
        })());
        // inspected is transformed to subset space
        const inspected_subset_indices = arrayable_1.filter(indices, (i) => inspected_full_indices.has(this.all_indices[i]));
        const { lod_threshold } = this.plot_model;
        let glyph;
        let nonselection_glyph;
        let selection_glyph;
        if ((this.model.document != null ? this.model.document.interactive_duration() > 0 : false)
            && !glsupport && lod_threshold != null && this.all_indices.length > lod_threshold) {
            // Render decimated during interaction if too many elements and not using GL
            indices = this.decimated;
            glyph = this.decimated_glyph;
            nonselection_glyph = this.decimated_glyph;
            selection_glyph = this.selection_glyph;
        }
        else {
            glyph = this.model.muted && this.muted_glyph != null ? this.muted_glyph : this.glyph;
            nonselection_glyph = this.nonselection_glyph;
            selection_glyph = this.selection_glyph;
        }
        if (this.hover_glyph != null && inspected_subset_indices.length)
            indices = array_1.difference(indices, inspected_subset_indices);
        // Render with no selection
        let dtselect = null;
        let trender;
        if (!(selected_full_indices.length && this.have_selection_glyphs())) {
            trender = Date.now();
            if (this.glyph instanceof line_1.LineView) {
                if (this.hover_glyph && inspected_subset_indices.length)
                    this.hover_glyph.render(ctx, this.model.view.convert_indices_from_subset(inspected_subset_indices), this.glyph);
                else
                    glyph.render(ctx, this.all_indices, this.glyph);
            }
            else if (this.glyph instanceof patch_1.PatchView || this.glyph instanceof harea_1.HAreaView || this.glyph instanceof varea_1.VAreaView) {
                if (inspected.selected_glyphs.length == 0 || this.hover_glyph == null) {
                    glyph.render(ctx, this.all_indices, this.glyph);
                }
                else {
                    for (const sglyph of inspected.selected_glyphs) {
                        if (sglyph.id == this.glyph.model.id)
                            this.hover_glyph.render(ctx, this.all_indices, this.glyph);
                    }
                }
            }
            else {
                glyph.render(ctx, indices, this.glyph);
                if (this.hover_glyph && inspected_subset_indices.length)
                    this.hover_glyph.render(ctx, inspected_subset_indices, this.glyph);
            }
            // Render with selection
        }
        else {
            // reset the selection mask
            const tselect = Date.now();
            const selected_mask = {};
            for (const i of selected_full_indices) {
                selected_mask[i] = true;
            }
            // intersect/different selection with render mask
            const selected_subset_indices = new Array();
            const nonselected_subset_indices = new Array();
            // now, selected is changed to subset space, except for Line glyph
            if (this.glyph instanceof line_1.LineView) {
                for (const i of this.all_indices) {
                    if (selected_mask[i] != null)
                        selected_subset_indices.push(i);
                    else
                        nonselected_subset_indices.push(i);
                }
            }
            else {
                for (const i of indices) {
                    if (selected_mask[this.all_indices[i]] != null)
                        selected_subset_indices.push(i);
                    else
                        nonselected_subset_indices.push(i);
                }
            }
            dtselect = Date.now() - tselect;
            trender = Date.now();
            nonselection_glyph.render(ctx, nonselected_subset_indices, this.glyph);
            selection_glyph.render(ctx, selected_subset_indices, this.glyph);
            if (this.hover_glyph != null) {
                if (this.glyph instanceof line_1.LineView)
                    this.hover_glyph.render(ctx, this.model.view.convert_indices_from_subset(inspected_subset_indices), this.glyph);
                else
                    this.hover_glyph.render(ctx, inspected_subset_indices, this.glyph);
            }
        }
        const dtrender = Date.now() - trender;
        this.last_dtrender = dtrender;
        const dttot = Date.now() - t0;
        logging_1.logger.debug(`${this.glyph.model.type} GlyphRenderer (${this.model.id}): render finished in ${dttot}ms`);
        logging_1.logger.trace(` - map_data finished in       : ${dtmap}ms`);
        logging_1.logger.trace(` - mask_data finished in      : ${dtmask}ms`);
        if (dtselect != null) {
            logging_1.logger.trace(` - selection mask finished in : ${dtselect}ms`);
        }
        logging_1.logger.trace(` - glyph renders finished in  : ${dtrender}ms`);
        ctx.restore();
    }
    draw_legend(ctx, x0, x1, y0, y1, field, label, index) {
        if (index == null)
            index = this.model.get_reference_point(field, label);
        this.glyph.draw_legend_for_index(ctx, { x0, x1, y0, y1 }, index);
    }
    hit_test(geometry) {
        if (!this.model.visible)
            return null;
        const hit_test_result = this.glyph.hit_test(geometry);
        // glyphs that don't have hit-testing implemented will return null
        if (hit_test_result == null)
            return null;
        return this.model.view.convert_selection_from_subset(hit_test_result);
    }
}
exports.GlyphRendererView = GlyphRendererView;
GlyphRendererView.__name__ = "GlyphRendererView";
class GlyphRenderer extends data_renderer_1.DataRenderer {
    constructor(attrs) {
        super(attrs);
    }
    static init_GlyphRenderer() {
        this.prototype.default_view = GlyphRendererView;
        this.define({
            data_source: [p.Instance],
            view: [p.Instance, () => new cds_view_1.CDSView()],
            glyph: [p.Instance],
            hover_glyph: [p.Instance],
            nonselection_glyph: [p.Any, 'auto'],
            selection_glyph: [p.Any, 'auto'],
            muted_glyph: [p.Instance],
            muted: [p.Boolean, false],
        });
    }
    initialize() {
        super.initialize();
        if (this.view.source == null) {
            this.view.source = this.data_source;
            this.view.compute_indices();
        }
    }
    get_reference_point(field, value) {
        let index = 0;
        if (field != null) {
            const data = this.data_source.get_column(field);
            if (data != null) {
                const i = arrayable_1.indexOf(data, value);
                if (i != -1)
                    index = i;
            }
        }
        return index;
    }
    get_selection_manager() {
        return this.data_source.selection_manager;
    }
}
exports.GlyphRenderer = GlyphRenderer;
GlyphRenderer.__name__ = "GlyphRenderer";
GlyphRenderer.init_GlyphRenderer();
