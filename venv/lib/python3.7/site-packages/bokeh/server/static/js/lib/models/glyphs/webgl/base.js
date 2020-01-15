"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const color_1 = require("../../../core/util/color");
const logging_1 = require("../../../core/logging");
class BaseGLGlyph {
    constructor(gl, glyph) {
        this.gl = gl;
        this.glyph = glyph;
        this.nvertices = 0;
        this.size_changed = false;
        this.data_changed = false;
        this.visuals_changed = false;
        this.init();
    }
    set_data_changed(n) {
        if (n != this.nvertices) {
            this.nvertices = n;
            this.size_changed = true;
        }
        this.data_changed = true;
    }
    set_visuals_changed() {
        this.visuals_changed = true;
    }
    render(_ctx, indices, mainglyph) {
        // Get transform
        const [a, b, c] = [0, 1, 2];
        let wx = 1; // Weights to scale our vectors
        let wy = 1;
        let [dx, dy] = this.glyph.renderer.map_to_screen([a * wx, b * wx, c * wx], [a * wy, b * wy, c * wy]);
        if (isNaN(dx[0] + dx[1] + dx[2] + dy[0] + dy[1] + dy[2])) {
            logging_1.logger.warn(`WebGL backend (${this.glyph.model.type}): falling back to canvas rendering`);
            return false;
        }
        // Try again, but with weighs so we're looking at ~100 in screen coordinates
        wx = 100 / Math.min(Math.max(Math.abs(dx[1] - dx[0]), 1e-12), 1e12);
        wy = 100 / Math.min(Math.max(Math.abs(dy[1] - dy[0]), 1e-12), 1e12);
        [dx, dy] = this.glyph.renderer.map_to_screen([a * wx, b * wx, c * wx], [a * wy, b * wy, c * wy]);
        // Test how linear it is
        if ((Math.abs((dx[1] - dx[0]) - (dx[2] - dx[1])) > 1e-6) ||
            (Math.abs((dy[1] - dy[0]) - (dy[2] - dy[1])) > 1e-6)) {
            logging_1.logger.warn(`WebGL backend (${this.glyph.model.type}): falling back to canvas rendering`);
            return false;
        }
        const [sx, sy] = [(dx[1] - dx[0]) / wx, (dy[1] - dy[0]) / wy];
        const { width, height } = this.glyph.renderer.plot_view.gl.canvas;
        const trans = {
            pixel_ratio: this.glyph.renderer.plot_view.canvas.pixel_ratio,
            width, height,
            dx: dx[0] / sx, dy: dy[0] / sy, sx, sy,
        };
        this.draw(indices, mainglyph, trans);
        return true;
    }
}
exports.BaseGLGlyph = BaseGLGlyph;
BaseGLGlyph.__name__ = "BaseGLGlyph";
function line_width(width) {
    // Increase small values to make it more similar to canvas
    if (width < 2) {
        width = Math.sqrt(width * 2);
    }
    return width;
}
exports.line_width = line_width;
function fill_array_with_float(n, val) {
    const a = new Float32Array(n);
    for (let i = 0, end = n; i < end; i++) {
        a[i] = val;
    }
    return a;
}
exports.fill_array_with_float = fill_array_with_float;
function fill_array_with_vec(n, m, val) {
    const a = new Float32Array(n * m);
    for (let i = 0; i < n; i++) {
        for (let j = 0; j < m; j++) {
            a[i * m + j] = val[j];
        }
    }
    return a;
}
exports.fill_array_with_vec = fill_array_with_vec;
function visual_prop_is_singular(visual, propname) {
    // This touches the internals of the visual, so we limit use in this function
    // See renderer.ts:cache_select() for similar code
    return visual[propname].spec.value !== undefined;
}
exports.visual_prop_is_singular = visual_prop_is_singular;
function attach_float(prog, vbo, att_name, n, visual, name) {
    // Attach a float attribute to the program. Use singleton value if we can,
    // otherwise use VBO to apply array.
    if (!visual.doit) {
        vbo.used = false;
        prog.set_attribute(att_name, 'float', [0]);
    }
    else if (visual_prop_is_singular(visual, name)) {
        vbo.used = false;
        prog.set_attribute(att_name, 'float', visual[name].value());
    }
    else {
        vbo.used = true;
        const a = new Float32Array(visual.cache[name + '_array']);
        vbo.set_size(n * 4);
        vbo.set_data(0, a);
        prog.set_attribute(att_name, 'float', vbo);
    }
}
exports.attach_float = attach_float;
function attach_color(prog, vbo, att_name, n, visual, prefix) {
    // Attach the color attribute to the program. If there's just one color,
    // then use this single color for all vertices (no VBO). Otherwise we
    // create an array and upload that to the VBO, which we attahce to the prog.
    let rgba;
    const m = 4;
    const colorname = prefix + '_color';
    const alphaname = prefix + '_alpha';
    if (!visual.doit) {
        // Don't draw (draw transparent)
        vbo.used = false;
        prog.set_attribute(att_name, 'vec4', [0, 0, 0, 0]);
    }
    else if (visual_prop_is_singular(visual, colorname) && visual_prop_is_singular(visual, alphaname)) {
        // Nice and simple; both color and alpha are singular
        vbo.used = false;
        rgba = color_1.color2rgba(visual[colorname].value(), visual[alphaname].value());
        prog.set_attribute(att_name, 'vec4', rgba);
    }
    else {
        // Use vbo; we need an array for both the color and the alpha
        let alphas, colors;
        vbo.used = true;
        // Get array of colors
        if (visual_prop_is_singular(visual, colorname)) {
            colors = ((() => {
                const result = [];
                for (let i = 0, end = n; i < end; i++) {
                    result.push(visual[colorname].value());
                }
                return result;
            })());
        }
        else {
            colors = visual.cache[colorname + '_array'];
        }
        // Get array of alphas
        if (visual_prop_is_singular(visual, alphaname)) {
            alphas = fill_array_with_float(n, visual[alphaname].value());
        }
        else {
            alphas = visual.cache[alphaname + '_array'];
        }
        // Create array of rgbs
        const a = new Float32Array(n * m);
        for (let i = 0, end = n; i < end; i++) {
            rgba = color_1.color2rgba(colors[i], alphas[i]);
            for (let j = 0, endj = m; j < endj; j++) {
                a[(i * m) + j] = rgba[j];
            }
        }
        // Attach vbo
        vbo.set_size(n * m * 4);
        vbo.set_data(0, a);
        prog.set_attribute(att_name, 'vec4', vbo);
    }
}
exports.attach_color = attach_color;
