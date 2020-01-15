"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const document_1 = require("../document");
const embed = require("../embed");
const models = require("./models");
const properties_1 = require("../core/properties");
const string_1 = require("../core/util/string");
const eq_1 = require("../core/util/eq");
const array_1 = require("../core/util/array");
const object_1 = require("../core/util/object");
const types_1 = require("../core/util/types");
const models_1 = require("./models");
const legend_1 = require("../models/annotations/legend");
var gridplot_1 = require("./gridplot");
exports.gridplot = gridplot_1.gridplot;
var color_1 = require("../core/util/color");
exports.color = color_1.rgb2hex;
const _default_tooltips = [
    ["index", "$index"],
    ["data (x, y)", "($x, $y)"],
    ["screen (x, y)", "($sx, $sy)"],
];
const _default_tools = ["pan", "wheel_zoom", "box_zoom", "save", "reset", "help"];
const _known_tools = {
    pan: () => new models.PanTool({ dimensions: 'both' }),
    xpan: () => new models.PanTool({ dimensions: 'width' }),
    ypan: () => new models.PanTool({ dimensions: 'height' }),
    xwheel_pan: () => new models.WheelPanTool({ dimension: "width" }),
    ywheel_pan: () => new models.WheelPanTool({ dimension: "height" }),
    wheel_zoom: () => new models.WheelZoomTool({ dimensions: 'both' }),
    xwheel_zoom: () => new models.WheelZoomTool({ dimensions: 'width' }),
    ywheel_zoom: () => new models.WheelZoomTool({ dimensions: 'height' }),
    zoom_in: () => new models.ZoomInTool({ dimensions: 'both' }),
    xzoom_in: () => new models.ZoomInTool({ dimensions: 'width' }),
    yzoom_in: () => new models.ZoomInTool({ dimensions: 'height' }),
    zoom_out: () => new models.ZoomOutTool({ dimensions: 'both' }),
    xzoom_out: () => new models.ZoomOutTool({ dimensions: 'width' }),
    yzoom_out: () => new models.ZoomOutTool({ dimensions: 'height' }),
    click: () => new models.TapTool({ behavior: "inspect" }),
    tap: () => new models.TapTool(),
    crosshair: () => new models.CrosshairTool(),
    box_select: () => new models.BoxSelectTool(),
    xbox_select: () => new models.BoxSelectTool({ dimensions: 'width' }),
    ybox_select: () => new models.BoxSelectTool({ dimensions: 'height' }),
    poly_select: () => new models.PolySelectTool(),
    lasso_select: () => new models.LassoSelectTool(),
    box_zoom: () => new models.BoxZoomTool({ dimensions: 'both' }),
    xbox_zoom: () => new models.BoxZoomTool({ dimensions: 'width' }),
    ybox_zoom: () => new models.BoxZoomTool({ dimensions: 'height' }),
    hover: () => new models.HoverTool({ tooltips: _default_tooltips }),
    save: () => new models.SaveTool(),
    undo: () => new models.UndoTool(),
    redo: () => new models.RedoTool(),
    reset: () => new models.ResetTool(),
    help: () => new models.HelpTool(),
};
const _default_color = "#1f77b4";
const _default_alpha = 1.0;
function _with_default(value, default_value) {
    return value === undefined ? default_value : value;
}
class Figure extends models_1.Plot {
    constructor(attrs = {}) {
        attrs = Object.assign({}, attrs);
        const tools = _with_default(attrs.tools, _default_tools);
        delete attrs.tools;
        const x_axis_type = _with_default(attrs.x_axis_type, "auto");
        const y_axis_type = _with_default(attrs.y_axis_type, "auto");
        delete attrs.x_axis_type;
        delete attrs.y_axis_type;
        const x_minor_ticks = attrs.x_minor_ticks != null ? attrs.x_minor_ticks : "auto";
        const y_minor_ticks = attrs.y_minor_ticks != null ? attrs.y_minor_ticks : "auto";
        delete attrs.x_minor_ticks;
        delete attrs.y_minor_ticks;
        const x_axis_location = attrs.x_axis_location != null ? attrs.x_axis_location : "below";
        const y_axis_location = attrs.y_axis_location != null ? attrs.y_axis_location : "left";
        delete attrs.x_axis_location;
        delete attrs.y_axis_location;
        const x_axis_label = attrs.x_axis_label != null ? attrs.x_axis_label : "";
        const y_axis_label = attrs.y_axis_label != null ? attrs.y_axis_label : "";
        delete attrs.x_axis_label;
        delete attrs.y_axis_label;
        const x_range = Figure._get_range(attrs.x_range);
        const y_range = Figure._get_range(attrs.y_range);
        delete attrs.x_range;
        delete attrs.y_range;
        const x_scale = attrs.x_scale != null ? attrs.x_scale : Figure._get_scale(x_range, x_axis_type);
        const y_scale = attrs.y_scale != null ? attrs.y_scale : Figure._get_scale(y_range, y_axis_type);
        delete attrs.x_scale;
        delete attrs.y_scale;
        super(Object.assign(Object.assign({}, attrs), { x_range, y_range, x_scale, y_scale }));
        this._process_axis_and_grid(x_axis_type, x_axis_location, x_minor_ticks, x_axis_label, x_range, 0);
        this._process_axis_and_grid(y_axis_type, y_axis_location, y_minor_ticks, y_axis_label, y_range, 1);
        this.add_tools(...this._process_tools(tools));
    }
    get xgrid() {
        return this.center.filter((r) => r instanceof models_1.Grid && r.dimension == 0);
    }
    get ygrid() {
        return this.center.filter((r) => r instanceof models_1.Grid && r.dimension == 1);
    }
    get xaxis() {
        return this.below.concat(this.above).filter((r) => r instanceof models_1.Axis);
    }
    get yaxis() {
        return this.left.concat(this.right).filter((r) => r instanceof models_1.Axis);
    }
    get legend() {
        const legends = this.panels.filter((r) => r instanceof legend_1.Legend);
        if (legends.length == 0) {
            const legend = new legend_1.Legend();
            this.add_layout(legend);
            return legend;
        }
        else {
            const [legend] = legends;
            return legend;
        }
    }
    annular_wedge(...args) {
        return this._glyph(models.AnnularWedge, "x,y,inner_radius,outer_radius,start_angle,end_angle", args);
    }
    annulus(...args) {
        return this._glyph(models.Annulus, "x,y,inner_radius,outer_radius", args);
    }
    arc(...args) {
        return this._glyph(models.Arc, "x,y,radius,start_angle,end_angle", args);
    }
    bezier(...args) {
        return this._glyph(models.Bezier, "x0,y0,x1,y1,cx0,cy0,cx1,cy1", args);
    }
    circle(...args) {
        return this._glyph(models.Circle, "x,y", args);
    }
    ellipse(...args) {
        return this._glyph(models.Ellipse, "x,y,width,height", args);
    }
    hbar(...args) {
        return this._glyph(models.HBar, "y,height,right,left", args);
    }
    hex_tile(...args) {
        return this._glyph(models.HexTile, "q,r", args);
    }
    image(...args) {
        return this._glyph(models.Image, "color_mapper,image,rows,cols,x,y,dw,dh", args);
    }
    image_rgba(...args) {
        return this._glyph(models.ImageRGBA, "image,rows,cols,x,y,dw,dh", args);
    }
    image_url(...args) {
        return this._glyph(models.ImageURL, "url,x,y,w,h", args);
    }
    line(...args) {
        return this._glyph(models.Line, "x,y", args);
    }
    multi_line(...args) {
        return this._glyph(models.MultiLine, "xs,ys", args);
    }
    multi_polygons(...args) {
        return this._glyph(models.MultiPolygons, "xs,ys", args);
    }
    oval(...args) {
        return this._glyph(models.Oval, "x,y,width,height", args);
    }
    patch(...args) {
        return this._glyph(models.Patch, "x,y", args);
    }
    patches(...args) {
        return this._glyph(models.Patches, "xs,ys", args);
    }
    quad(...args) {
        return this._glyph(models.Quad, "left,right,bottom,top", args);
    }
    quadratic(...args) {
        return this._glyph(models.Quadratic, "x0,y0,x1,y1,cx,cy", args);
    }
    ray(...args) {
        return this._glyph(models.Ray, "x,y,length", args);
    }
    rect(...args) {
        return this._glyph(models.Rect, "x,y,width,height", args);
    }
    segment(...args) {
        return this._glyph(models.Segment, "x0,y0,x1,y1", args);
    }
    step(...args) {
        return this._glyph(models.Step, "x,y,mode", args);
    }
    text(...args) {
        return this._glyph(models.Text, "x,y,text", args);
    }
    vbar(...args) {
        return this._glyph(models.VBar, "x,width,top,bottom", args);
    }
    wedge(...args) {
        return this._glyph(models.Wedge, "x,y,radius,start_angle,end_angle", args);
    }
    asterisk(...args) {
        return this._marker(models.Asterisk, args);
    }
    circle_cross(...args) {
        return this._marker(models.CircleCross, args);
    }
    circle_x(...args) {
        return this._marker(models.CircleX, args);
    }
    cross(...args) {
        return this._marker(models.Cross, args);
    }
    dash(...args) {
        return this._marker(models.Dash, args);
    }
    diamond(...args) {
        return this._marker(models.Diamond, args);
    }
    diamond_cross(...args) {
        return this._marker(models.DiamondCross, args);
    }
    inverted_triangle(...args) {
        return this._marker(models.InvertedTriangle, args);
    }
    square(...args) {
        return this._marker(models.Square, args);
    }
    square_cross(...args) {
        return this._marker(models.SquareCross, args);
    }
    square_x(...args) {
        return this._marker(models.SquareX, args);
    }
    triangle(...args) {
        return this._marker(models.Triangle, args);
    }
    x(...args) {
        return this._marker(models.X, args);
    }
    scatter(...args) {
        return this._marker(models.Scatter, args);
    }
    _pop_colors_and_alpha(cls, attrs, prefix = "", default_color = _default_color, default_alpha = _default_alpha) {
        const result = {};
        const color = _with_default(attrs[prefix + "color"], default_color);
        const alpha = _with_default(attrs[prefix + "alpha"], default_alpha);
        delete attrs[prefix + "color"];
        delete attrs[prefix + "alpha"];
        const _update_with = function (name, default_value) {
            if (cls.prototype.props[name] != null) {
                result[name] = _with_default(attrs[prefix + name], default_value);
                delete attrs[prefix + name];
            }
        };
        _update_with("fill_color", color);
        _update_with("line_color", color);
        _update_with("text_color", "black");
        _update_with("fill_alpha", alpha);
        _update_with("line_alpha", alpha);
        _update_with("text_alpha", alpha);
        return result;
    }
    _find_uniq_name(data, name) {
        let i = 1;
        while (true) {
            const new_name = `${name}__${i}`;
            if (data[new_name] != null) {
                i += 1;
            }
            else {
                return new_name;
            }
        }
    }
    _fixup_values(cls, data, attrs) {
        for (const name in attrs) {
            const value = attrs[name];
            const prop = cls.prototype.props[name];
            if (prop != null) {
                if (prop.type.prototype instanceof properties_1.VectorSpec) {
                    if (value != null) {
                        if (types_1.isArray(value)) {
                            let field;
                            if (data[name] != null) {
                                if (data[name] !== value) {
                                    field = this._find_uniq_name(data, name);
                                    data[field] = value;
                                }
                                else {
                                    field = name;
                                }
                            }
                            else {
                                field = name;
                                data[field] = value;
                            }
                            attrs[name] = { field };
                        }
                        else if (types_1.isNumber(value) || types_1.isString(value)) { // or Date?
                            attrs[name] = { value };
                        }
                    }
                }
            }
        }
    }
    _glyph(cls, params_string, args) {
        const params = params_string.split(",");
        let attrs;
        if (args.length == 0) {
            attrs = {};
        }
        else if (args.length == 1) {
            attrs = object_1.clone(args[0]);
        }
        else {
            attrs = object_1.clone(args[args.length - 1]);
            for (let i = 0; i < params.length; i++) {
                const param = params[i];
                attrs[param] = args[i];
            }
        }
        const source = attrs.source != null ? attrs.source : new models.ColumnDataSource();
        const data = object_1.clone(source.data);
        delete attrs.source;
        const legend = this._process_legend(attrs.legend, source);
        delete attrs.legend;
        const has_sglyph = array_1.some(Object.keys(attrs), key => string_1.startsWith(key, "selection_"));
        const has_hglyph = array_1.some(Object.keys(attrs), key => string_1.startsWith(key, "hover_"));
        const glyph_ca = this._pop_colors_and_alpha(cls, attrs);
        const nsglyph_ca = this._pop_colors_and_alpha(cls, attrs, "nonselection_", undefined, 0.1);
        const sglyph_ca = has_sglyph ? this._pop_colors_and_alpha(cls, attrs, "selection_") : {};
        const hglyph_ca = has_hglyph ? this._pop_colors_and_alpha(cls, attrs, "hover_") : {};
        this._fixup_values(cls, data, glyph_ca);
        this._fixup_values(cls, data, nsglyph_ca);
        this._fixup_values(cls, data, sglyph_ca);
        this._fixup_values(cls, data, hglyph_ca);
        this._fixup_values(cls, data, attrs);
        source.data = data;
        const _make_glyph = (cls, attrs, extra_attrs) => {
            return new cls(Object.assign(Object.assign({}, attrs), extra_attrs));
        };
        const glyph = _make_glyph(cls, attrs, glyph_ca);
        const nsglyph = _make_glyph(cls, attrs, nsglyph_ca);
        const sglyph = has_sglyph ? _make_glyph(cls, attrs, sglyph_ca) : undefined;
        const hglyph = has_hglyph ? _make_glyph(cls, attrs, hglyph_ca) : undefined;
        const glyph_renderer = new models_1.GlyphRenderer({
            data_source: source,
            glyph,
            nonselection_glyph: nsglyph,
            selection_glyph: sglyph,
            hover_glyph: hglyph,
        });
        if (legend != null) {
            this._update_legend(legend, glyph_renderer);
        }
        this.add_renderers(glyph_renderer);
        return glyph_renderer;
    }
    _marker(cls, args) {
        return this._glyph(cls, "x,y", args);
    }
    static _get_range(range) {
        if (range == null) {
            return new models.DataRange1d();
        }
        if (range instanceof models.Range) {
            return range;
        }
        if (types_1.isArray(range)) {
            if (array_1.every(range, types_1.isString)) {
                const factors = range;
                return new models.FactorRange({ factors });
            }
            if (range.length == 2) {
                const [start, end] = range;
                return new models.Range1d({ start, end });
            }
        }
        throw new Error(`unable to determine proper range for: '${range}'`);
    }
    static _get_scale(range_input, axis_type) {
        if (range_input instanceof models.DataRange1d ||
            range_input instanceof models.Range1d) {
            switch (axis_type) {
                case null:
                case "auto":
                case "linear":
                case "datetime":
                    return new models.LinearScale();
                case "log":
                    return new models.LogScale();
            }
        }
        if (range_input instanceof models.FactorRange) {
            return new models.CategoricalScale();
        }
        throw new Error(`unable to determine proper scale for: '${range_input}'`);
    }
    _process_axis_and_grid(axis_type, axis_location, minor_ticks, axis_label, rng, dim) {
        const axiscls = this._get_axis_class(axis_type, rng);
        if (axiscls != null) {
            if (axiscls === models.LogAxis) {
                if (dim === 0) {
                    this.x_scale = new models.LogScale();
                }
                else {
                    this.y_scale = new models.LogScale();
                }
            }
            const axis = new axiscls();
            if (axis.ticker instanceof models.ContinuousTicker) {
                axis.ticker.num_minor_ticks = this._get_num_minor_ticks(axiscls, minor_ticks);
            }
            if (axis_label.length !== 0) {
                axis.axis_label = axis_label;
            }
            const grid = new models.Grid({ dimension: dim, ticker: axis.ticker });
            if (axis_location !== null) {
                this.add_layout(axis, axis_location);
            }
            this.add_layout(grid);
        }
    }
    _get_axis_class(axis_type, range) {
        switch (axis_type) {
            case null:
                return null;
            case "linear":
                return models.LinearAxis;
            case "log":
                return models.LogAxis;
            case "datetime":
                return models.DatetimeAxis;
            case "auto":
                if (range instanceof models.FactorRange)
                    return models.CategoricalAxis;
                else
                    return models.LinearAxis; // TODO: return models.DatetimeAxis (Date type)
            default:
                throw new Error("shouldn't have happened");
        }
    }
    _get_num_minor_ticks(axis_class, num_minor_ticks) {
        if (types_1.isNumber(num_minor_ticks)) {
            if (num_minor_ticks <= 1) {
                throw new Error("num_minor_ticks must be > 1");
            }
            return num_minor_ticks;
        }
        if (num_minor_ticks == null) {
            return 0;
        }
        if (num_minor_ticks === 'auto') {
            if (axis_class === models.LogAxis) {
                return 10;
            }
            return 5;
        }
        throw new Error("shouldn't have happened");
    }
    _process_tools(tools) {
        if (types_1.isString(tools))
            tools = tools.split(/\s*,\s*/).filter((tool) => tool.length > 0);
        function isToolName(tool) {
            return _known_tools.hasOwnProperty(tool);
        }
        const objs = (() => {
            const result = [];
            for (const tool of tools) {
                if (types_1.isString(tool)) {
                    if (isToolName(tool))
                        result.push(_known_tools[tool]());
                    else
                        throw new Error(`unknown tool type: ${tool}`);
                }
                else
                    result.push(tool);
            }
            return result;
        })();
        return objs;
    }
    _process_legend(legend, source) {
        let legend_item_label = null;
        if (legend != null) {
            if (types_1.isString(legend)) {
                legend_item_label = { value: legend };
                if (source.columns() != null) {
                    if (array_1.includes(source.columns(), legend)) {
                        legend_item_label = { field: legend };
                    }
                }
            }
            else {
                legend_item_label = legend;
            }
        }
        return legend_item_label;
    }
    _update_legend(legend_item_label, glyph_renderer) {
        const { legend } = this;
        let added = false;
        for (const item of legend.items) {
            if (item.label != null && eq_1.isEqual(item.label, legend_item_label)) {
                // XXX: remove this when vectorable properties are refined
                const label = item.label;
                if ("value" in label) {
                    item.renderers.push(glyph_renderer);
                    added = true;
                    break;
                }
                if ("field" in label && glyph_renderer.data_source == item.renderers[0].data_source) {
                    item.renderers.push(glyph_renderer);
                    added = true;
                    break;
                }
            }
        }
        if (!added) {
            const new_item = new models.LegendItem({ label: legend_item_label, renderers: [glyph_renderer] });
            legend.items.push(new_item);
        }
    }
}
exports.Figure = Figure;
Figure.__name__ = "Plot";
function figure(attributes) {
    return new Figure(attributes);
}
exports.figure = figure;
function show(obj, target) {
    const doc = new document_1.Document();
    for (const item of types_1.isArray(obj) ? obj : [obj])
        doc.add_root(item);
    let element;
    if (target == null) {
        element = document.body;
    }
    else if (types_1.isString(target)) {
        const found = document.querySelector(target);
        if (found != null && found instanceof HTMLElement)
            element = found;
        else
            throw new Error(`'${target}' selector didn't match any elements`);
    }
    else if (target instanceof HTMLElement) {
        element = target;
    }
    else if (typeof $ !== 'undefined' && target instanceof $) {
        element = target[0];
    }
    else {
        throw new Error("target should be HTMLElement, string selector, $ or null");
    }
    const views = object_1.values(embed.add_document_standalone(doc, element)); // XXX
    return new Promise((resolve, _reject) => {
        const result = types_1.isArray(obj) ? views : views[0];
        if (doc.is_idle)
            resolve(result);
        else
            doc.idle.connect(() => resolve(result));
    });
}
exports.show = show;
