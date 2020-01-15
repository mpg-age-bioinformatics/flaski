"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const mixins = require("./property_mixins");
const color_1 = require("./util/color");
function _horz(ctx, h, h2) {
    ctx.moveTo(0, h2 + 0.5);
    ctx.lineTo(h, h2 + 0.5);
    ctx.stroke();
}
function _vert(ctx, h, h2) {
    ctx.moveTo(h2 + 0.5, 0);
    ctx.lineTo(h2 + 0.5, h);
    ctx.stroke();
}
function _x(ctx, h) {
    ctx.moveTo(0, h);
    ctx.lineTo(h, 0);
    ctx.stroke();
    ctx.moveTo(0, 0);
    ctx.lineTo(h, h);
    ctx.stroke();
}
function _get_canvas(size) {
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    return canvas;
}
function create_hatch_canvas(hatch_pattern, hatch_color, hatch_scale, hatch_weight) {
    const h = hatch_scale;
    const h2 = h / 2;
    const h4 = h2 / 2;
    const canvas = _get_canvas(hatch_scale);
    const ctx = canvas.getContext("2d");
    ctx.strokeStyle = hatch_color;
    ctx.lineCap = "square";
    ctx.fillStyle = hatch_color;
    ctx.lineWidth = hatch_weight;
    switch (hatch_pattern) {
        // we should not need these if code conditions on hatch.doit, but
        // include them here just for completeness
        case " ":
        case "blank":
            break;
        case ".":
        case "dot":
            ctx.arc(h2, h2, h2 / 2, 0, 2 * Math.PI, true);
            ctx.fill();
            break;
        case "o":
        case "ring":
            ctx.arc(h2, h2, h2 / 2, 0, 2 * Math.PI, true);
            ctx.stroke();
            break;
        case "-":
        case "horizontal_line":
            _horz(ctx, h, h2);
            break;
        case "|":
        case "vertical_line":
            _vert(ctx, h, h2);
            break;
        case "+":
        case "cross":
            _horz(ctx, h, h2);
            _vert(ctx, h, h2);
            break;
        case "\"":
        case "horizontal_dash":
            _horz(ctx, h2, h2);
            break;
        case ":":
        case "vertical_dash":
            _vert(ctx, h2, h2);
            break;
        case "@":
        case "spiral":
            const h30 = h / 30;
            ctx.moveTo(h2, h2);
            for (let i = 0; i < 360; i++) {
                const angle = 0.1 * i;
                const x = h2 + (h30 * angle) * Math.cos(angle);
                const y = h2 + (h30 * angle) * Math.sin(angle);
                ctx.lineTo(x, y);
            }
            ctx.stroke();
            break;
        case "/":
        case "right_diagonal_line":
            ctx.moveTo(-h4 + 0.5, h);
            ctx.lineTo(h4 + 0.5, 0);
            ctx.stroke();
            ctx.moveTo(h4 + 0.5, h);
            ctx.lineTo(3 * h4 + 0.5, 0);
            ctx.stroke();
            ctx.moveTo(3 * h4 + 0.5, h);
            ctx.lineTo(5 * h4 + 0.5, 0);
            ctx.stroke();
            ctx.stroke();
            break;
        case "\\":
        case "left_diagonal_line":
            ctx.moveTo(h4 + 0.5, h);
            ctx.lineTo(-h4 + 0.5, 0);
            ctx.stroke();
            ctx.moveTo(3 * h4 + 0.5, h);
            ctx.lineTo(h4 + 0.5, 0);
            ctx.stroke();
            ctx.moveTo(5 * h4 + 0.5, h);
            ctx.lineTo(3 * h4 + 0.5, 0);
            ctx.stroke();
            ctx.stroke();
            break;
        case "x":
        case "diagonal_cross":
            _x(ctx, h);
            break;
        case ",":
        case "right_diagonal_dash":
            ctx.moveTo(h4 + 0.5, 3 * h4 + 0.5);
            ctx.lineTo(3 * h4 + 0.5, h4 + 0.5);
            ctx.stroke();
            break;
        case "`":
        case "left_diagonal_dash":
            ctx.moveTo(h4 + 0.5, h4 + 0.5);
            ctx.lineTo(3 * h4 + 0.5, 3 * h4 + 0.5);
            ctx.stroke();
            break;
        case "v":
        case "horizontal_wave":
            ctx.moveTo(0, h4);
            ctx.lineTo(h2, 3 * h4);
            ctx.lineTo(h, h4);
            ctx.stroke();
            break;
        case ">":
        case "vertical_wave":
            ctx.moveTo(h4, 0);
            ctx.lineTo(3 * h4, h2);
            ctx.lineTo(h4, h);
            ctx.stroke();
            break;
        case "*":
        case "criss_cross":
            _x(ctx, h);
            _horz(ctx, h, h2);
            _vert(ctx, h, h2);
            break;
    }
    return canvas;
}
class ContextProperties {
    constructor(obj, prefix = "") {
        this.obj = obj;
        this.prefix = prefix;
        // }
        this.cache = {};
        for (const attr of this.attrs)
            this[attr] = obj.properties[prefix + attr];
    }
    warm_cache(source) {
        for (const attr of this.attrs) {
            const prop = this.obj.properties[this.prefix + attr];
            if (prop.spec.value !== undefined) // TODO (bev) better test?
                this.cache[attr] = prop.spec.value;
            else if (source != null)
                this.cache[attr + "_array"] = prop.array(source);
            else
                throw new Error("source is required with a vectorized visual property");
        }
    }
    cache_select(attr, i) {
        const prop = this.obj.properties[this.prefix + attr];
        let value;
        if (prop.spec.value !== undefined) // TODO (bev) better test?
            this.cache[attr] = value = prop.spec.value;
        else
            this.cache[attr] = value = this.cache[attr + "_array"][i];
        return value;
    }
    set_vectorize(ctx, i) {
        if (this.all_indices != null) // all_indices is set by a Visuals instance associated with a CDSView
            this._set_vectorize(ctx, this.all_indices[i]);
        else // all_indices is not set for annotations which may have vectorized visual props
            this._set_vectorize(ctx, i);
    }
}
exports.ContextProperties = ContextProperties;
ContextProperties.__name__ = "ContextProperties";
class Line extends ContextProperties {
    set_value(ctx) {
        ctx.strokeStyle = this.line_color.value();
        ctx.globalAlpha = this.line_alpha.value();
        ctx.lineWidth = this.line_width.value();
        ctx.lineJoin = this.line_join.value();
        ctx.lineCap = this.line_cap.value();
        ctx.setLineDash(this.line_dash.value());
        ctx.setLineDashOffset(this.line_dash_offset.value());
    }
    get doit() {
        return !(this.line_color.spec.value === null ||
            this.line_alpha.spec.value == 0 ||
            this.line_width.spec.value == 0);
    }
    _set_vectorize(ctx, i) {
        this.cache_select("line_color", i);
        if (ctx.strokeStyle !== this.cache.line_color)
            ctx.strokeStyle = this.cache.line_color;
        this.cache_select("line_alpha", i);
        if (ctx.globalAlpha !== this.cache.line_alpha)
            ctx.globalAlpha = this.cache.line_alpha;
        this.cache_select("line_width", i);
        if (ctx.lineWidth !== this.cache.line_width)
            ctx.lineWidth = this.cache.line_width;
        this.cache_select("line_join", i);
        if (ctx.lineJoin !== this.cache.line_join)
            ctx.lineJoin = this.cache.line_join;
        this.cache_select("line_cap", i);
        if (ctx.lineCap !== this.cache.line_cap)
            ctx.lineCap = this.cache.line_cap;
        this.cache_select("line_dash", i);
        if (ctx.getLineDash() !== this.cache.line_dash)
            ctx.setLineDash(this.cache.line_dash);
        this.cache_select("line_dash_offset", i);
        if (ctx.getLineDashOffset() !== this.cache.line_dash_offset)
            ctx.setLineDashOffset(this.cache.line_dash_offset);
    }
    color_value() {
        const [r, g, b, a] = color_1.color2rgba(this.line_color.value(), this.line_alpha.value());
        return `rgba(${r * 255},${g * 255},${b * 255},${a})`;
    }
}
exports.Line = Line;
Line.__name__ = "Line";
Line.prototype.attrs = Object.keys(mixins.line());
class Fill extends ContextProperties {
    set_value(ctx) {
        ctx.fillStyle = this.fill_color.value();
        ctx.globalAlpha = this.fill_alpha.value();
    }
    get doit() {
        return !(this.fill_color.spec.value === null ||
            this.fill_alpha.spec.value == 0);
    }
    _set_vectorize(ctx, i) {
        this.cache_select("fill_color", i);
        if (ctx.fillStyle !== this.cache.fill_color)
            ctx.fillStyle = this.cache.fill_color;
        this.cache_select("fill_alpha", i);
        if (ctx.globalAlpha !== this.cache.fill_alpha)
            ctx.globalAlpha = this.cache.fill_alpha;
    }
    color_value() {
        const [r, g, b, a] = color_1.color2rgba(this.fill_color.value(), this.fill_alpha.value());
        return `rgba(${r * 255},${g * 255},${b * 255},${a})`;
    }
}
exports.Fill = Fill;
Fill.__name__ = "Fill";
Fill.prototype.attrs = Object.keys(mixins.fill());
class Hatch extends ContextProperties {
    cache_select(name, i) {
        let value;
        if (name == "pattern") {
            this.cache_select("hatch_color", i);
            this.cache_select("hatch_scale", i);
            this.cache_select("hatch_pattern", i);
            this.cache_select("hatch_weight", i);
            const { hatch_color, hatch_scale, hatch_pattern, hatch_weight, hatch_extra } = this.cache;
            if (hatch_extra != null && hatch_extra.hasOwnProperty(hatch_pattern)) {
                const custom = hatch_extra[hatch_pattern];
                this.cache.pattern = custom.get_pattern(hatch_color, hatch_scale, hatch_weight);
            }
            else {
                this.cache.pattern = (ctx) => {
                    const canvas = create_hatch_canvas(hatch_pattern, hatch_color, hatch_scale, hatch_weight);
                    return ctx.createPattern(canvas, 'repeat');
                };
            }
        }
        else
            value = super.cache_select(name, i);
        return value;
    }
    _try_defer(defer_func) {
        const { hatch_pattern, hatch_extra } = this.cache;
        if (hatch_extra != null && hatch_extra.hasOwnProperty(hatch_pattern)) {
            const custom = hatch_extra[hatch_pattern];
            custom.onload(defer_func);
        }
    }
    get doit() {
        return !(this.hatch_color.spec.value === null ||
            this.hatch_alpha.spec.value == 0 ||
            this.hatch_pattern.spec.value == " " ||
            this.hatch_pattern.spec.value == "blank" ||
            this.hatch_pattern.spec.value === null);
    }
    doit2(ctx, i, ready_func, defer_func) {
        if (!this.doit) {
            return;
        }
        this.cache_select("pattern", i);
        const pattern = this.cache.pattern(ctx);
        if (pattern == null) {
            this._try_defer(defer_func);
        }
        else {
            this.set_vectorize(ctx, i);
            ready_func();
        }
    }
    _set_vectorize(ctx, i) {
        this.cache_select("pattern", i);
        ctx.fillStyle = this.cache.pattern(ctx);
        this.cache_select("hatch_alpha", i);
        if (ctx.globalAlpha !== this.cache.hatch_alpha)
            ctx.globalAlpha = this.cache.hatch_alpha;
    }
    color_value() {
        const [r, g, b, a] = color_1.color2rgba(this.hatch_color.value(), this.hatch_alpha.value());
        return `rgba(${r * 255},${g * 255},${b * 255},${a})`;
    }
}
exports.Hatch = Hatch;
Hatch.__name__ = "Hatch";
Hatch.prototype.attrs = Object.keys(mixins.hatch());
class Text extends ContextProperties {
    cache_select(name, i) {
        let value;
        if (name == "font") {
            super.cache_select("text_font_style", i);
            super.cache_select("text_font_size", i);
            super.cache_select("text_font", i);
            const { text_font_style, text_font_size, text_font } = this.cache;
            this.cache.font = value = `${text_font_style} ${text_font_size} ${text_font}`;
        }
        else
            value = super.cache_select(name, i);
        return value;
    }
    font_value() {
        const font = this.text_font.value();
        const font_size = this.text_font_size.value();
        const font_style = this.text_font_style.value();
        return font_style + " " + font_size + " " + font;
    }
    color_value() {
        const [r, g, b, a] = color_1.color2rgba(this.text_color.value(), this.text_alpha.value());
        return `rgba(${r * 255},${g * 255},${b * 255},${a})`;
    }
    set_value(ctx) {
        ctx.font = this.font_value();
        ctx.fillStyle = this.text_color.value();
        ctx.globalAlpha = this.text_alpha.value();
        ctx.textAlign = this.text_align.value();
        ctx.textBaseline = this.text_baseline.value();
    }
    get doit() {
        return !(this.text_color.spec.value === null ||
            this.text_alpha.spec.value == 0);
    }
    _set_vectorize(ctx, i) {
        this.cache_select("font", i);
        if (ctx.font !== this.cache.font)
            ctx.font = this.cache.font;
        this.cache_select("text_color", i);
        if (ctx.fillStyle !== this.cache.text_color)
            ctx.fillStyle = this.cache.text_color;
        this.cache_select("text_alpha", i);
        if (ctx.globalAlpha !== this.cache.text_alpha)
            ctx.globalAlpha = this.cache.text_alpha;
        this.cache_select("text_align", i);
        if (ctx.textAlign !== this.cache.text_align)
            ctx.textAlign = this.cache.text_align;
        this.cache_select("text_baseline", i);
        if (ctx.textBaseline !== this.cache.text_baseline)
            ctx.textBaseline = this.cache.text_baseline;
    }
}
exports.Text = Text;
Text.__name__ = "Text";
Text.prototype.attrs = Object.keys(mixins.text());
class Visuals {
    constructor(model) {
        for (const mixin of model.mixins) {
            const [name, prefix = ""] = mixin.split(":");
            let cls;
            switch (name) {
                case "line":
                    cls = Line;
                    break;
                case "fill":
                    cls = Fill;
                    break;
                case "hatch":
                    cls = Hatch;
                    break;
                case "text":
                    cls = Text;
                    break;
                default:
                    throw new Error(`unknown visual: ${name}`);
            }
            this[prefix + name] = new cls(model, prefix);
        }
    }
    warm_cache(source) {
        for (const name in this) {
            if (this.hasOwnProperty(name)) {
                const prop = this[name];
                if (prop instanceof ContextProperties)
                    prop.warm_cache(source);
            }
        }
    }
    set_all_indices(all_indices) {
        for (const name in this) {
            if (this.hasOwnProperty(name)) {
                const prop = this[name];
                if (prop instanceof ContextProperties)
                    prop.all_indices = all_indices;
            }
        }
    }
}
exports.Visuals = Visuals;
Visuals.__name__ = "Visuals";
