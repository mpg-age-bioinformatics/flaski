"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const palettes = require("./palettes");
const array_1 = require("../core/util/array");
const types_1 = require("../core/util/types");
const templating_1 = require("../core/util/templating");
const models_1 = require("./models");
function num2hexcolor(num) {
    return templating_1.sprintf("#%06x", num);
}
function hexcolor2rgb(color) {
    const r = parseInt(color.substr(1, 2), 16);
    const g = parseInt(color.substr(3, 2), 16);
    const b = parseInt(color.substr(5, 2), 16);
    return [r, g, b];
}
function is_dark([r, g, b]) {
    const l = 1 - (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return l >= 0.6;
}
function norm_palette(palette = "Spectral11") {
    if (types_1.isArray(palette))
        return palette;
    else {
        return palettes[palette].map(num2hexcolor);
    }
}
function pie(data, opts = {}) {
    const labels = [];
    const values = [];
    for (let i = 0; i < Math.min(data.labels.length, data.values.length); i++) {
        if (data.values[i] > 0) {
            labels.push(data.labels[i]);
            values.push(data.values[i]);
        }
    }
    const start_angle = opts.start_angle != null ? opts.start_angle : 0;
    const end_angle = opts.end_angle != null ? opts.end_angle : (start_angle + 2 * Math.PI);
    const angle_span = Math.abs(end_angle - start_angle);
    const to_radians = (x) => angle_span * x;
    const total_value = array_1.sum(values);
    const normalized_values = values.map((v) => v / total_value);
    const cumulative_values = array_1.cumsum(normalized_values);
    const end_angles = cumulative_values.map((v) => start_angle + to_radians(v));
    const start_angles = [start_angle].concat(end_angles.slice(0, -1));
    const half_angles = array_1.zip(start_angles, end_angles).map(([start, end]) => (start + end) / 2);
    let cx;
    let cy;
    if (opts.center == null) {
        cx = 0;
        cy = 0;
    }
    else if (types_1.isArray(opts.center)) {
        cx = opts.center[0];
        cy = opts.center[1];
    }
    else {
        cx = opts.center.x;
        cy = opts.center.y;
    }
    const inner_radius = opts.inner_radius != null ? opts.inner_radius : 0;
    const outer_radius = opts.outer_radius != null ? opts.outer_radius : 1;
    const palette = norm_palette(opts.palette);
    const colors = [];
    for (let i = 0; i < normalized_values.length; i++)
        colors.push(palette[i % palette.length]);
    const text_colors = colors.map((c) => is_dark(hexcolor2rgb(c)) ? "white" : "black");
    function to_cartesian(r, alpha) {
        return [r * Math.cos(alpha), r * Math.sin(alpha)];
    }
    const half_radius = (inner_radius + outer_radius) / 2;
    let [text_cx, text_cy] = array_1.unzip(half_angles.map((half_angle) => to_cartesian(half_radius, half_angle)));
    text_cx = text_cx.map((x) => x + cx);
    text_cy = text_cy.map((y) => y + cy);
    const text_angles = half_angles.map((a) => {
        if (a >= Math.PI / 2 && a <= 3 * Math.PI / 2)
            return a + Math.PI;
        else
            return a;
    });
    const source = new models_1.ColumnDataSource({
        data: {
            labels,
            values,
            percentages: normalized_values.map((v) => templating_1.sprintf("%.2f%%", v * 100)),
            start_angles,
            end_angles,
            text_angles,
            colors,
            text_colors,
            text_cx,
            text_cy,
        },
    });
    const g1 = new models_1.AnnularWedge({
        x: cx, y: cy,
        inner_radius, outer_radius,
        start_angle: { field: "start_angles" }, end_angle: { field: "end_angles" },
        line_color: null, line_width: 1, fill_color: { field: "colors" },
    });
    const h1 = new models_1.AnnularWedge({
        x: cx, y: cy,
        inner_radius, outer_radius,
        start_angle: { field: "start_angles" }, end_angle: { field: "end_angles" },
        line_color: null, line_width: 1, fill_color: { field: "colors" }, fill_alpha: 0.8,
    });
    const r1 = new models_1.GlyphRenderer({
        data_source: source,
        glyph: g1,
        hover_glyph: h1,
    });
    const g2 = new models_1.Text({
        x: { field: "text_cx" }, y: { field: "text_cy" },
        text: { field: opts.slice_labels || "labels" },
        angle: { field: "text_angles" },
        text_align: "center", text_baseline: "middle",
        text_color: { field: "text_colors" }, text_font_size: "9pt",
    });
    const r2 = new models_1.GlyphRenderer({
        data_source: source,
        glyph: g2,
    });
    const xdr = new models_1.DataRange1d({ renderers: [r1], range_padding: 0.2 });
    const ydr = new models_1.DataRange1d({ renderers: [r1], range_padding: 0.2 });
    const plot = new models_1.Plot({ x_range: xdr, y_range: ydr });
    if (opts.width != null)
        plot.plot_width = opts.width;
    if (opts.height != null)
        plot.plot_height = opts.height;
    plot.add_renderers(r1, r2);
    const tooltip = "<div>@labels</div><div><b>@values</b> (@percentages)</div>";
    const hover = new models_1.HoverTool({ renderers: [r1], tooltips: tooltip });
    plot.add_tools(hover);
    return plot;
}
exports.pie = pie;
function bar(data, opts = {}) {
    const column_names = data[0];
    const row_data = data.slice(1);
    const col_data = array_1.transpose(row_data);
    const labels = col_data[0].map((v) => v.toString());
    const columns = col_data.slice(1);
    let yaxis = new models_1.CategoricalAxis();
    let ydr = new models_1.FactorRange({ factors: labels });
    let yscale = new models_1.CategoricalScale();
    let xformatter;
    if (opts.axis_number_format != null)
        xformatter = new models_1.NumeralTickFormatter({ format: opts.axis_number_format });
    else
        xformatter = new models_1.BasicTickFormatter();
    let xaxis = new models_1.LinearAxis({ formatter: xformatter });
    let xdr = new models_1.DataRange1d({ start: 0 });
    let xscale = new models_1.LinearScale();
    const palette = norm_palette(opts.palette);
    const stacked = opts.stacked != null ? opts.stacked : false;
    const orientation = opts.orientation != null ? opts.orientation : "horizontal";
    const renderers = [];
    if (stacked) {
        const left = [];
        const right = [];
        for (let i = 0; i < columns.length; i++) {
            const bottom = [];
            const top = [];
            for (let j = 0; j < labels.length; j++) {
                const label = labels[j];
                if (i == 0) {
                    left.push(0);
                    right.push(columns[i][j]);
                }
                else {
                    left[j] += columns[i - 1][j];
                    right[j] += columns[i][j];
                }
                bottom.push([label, -0.5]);
                top.push([label, 0.5]);
            }
            const source = new models_1.ColumnDataSource({
                data: {
                    left: array_1.copy(left),
                    right: array_1.copy(right),
                    top,
                    bottom,
                    labels,
                    values: columns[i],
                    columns: columns[i].map((_) => column_names[i + 1]),
                },
            });
            const g1 = new models_1.Quad({
                left: { field: "left" }, bottom: { field: "bottom" },
                right: { field: "right" }, top: { field: "top" },
                line_color: null, fill_color: palette[i % palette.length],
            });
            const r1 = new models_1.GlyphRenderer({ data_source: source, glyph: g1 });
            renderers.push(r1);
        }
    }
    else {
        const dy = 1 / columns.length;
        for (let i = 0; i < columns.length; i++) {
            const left = [];
            const right = [];
            const bottom = [];
            const top = [];
            for (let j = 0; j < labels.length; j++) {
                const label = labels[j];
                left.push(0);
                right.push(columns[i][j]);
                bottom.push([label, i * dy - 0.5]);
                top.push([label, (i + 1) * dy - 0.5]);
            }
            const source = new models_1.ColumnDataSource({
                data: {
                    left,
                    right,
                    top,
                    bottom,
                    labels,
                    values: columns[i],
                    columns: columns[i].map((_) => column_names[i + 1]),
                },
            });
            const g1 = new models_1.Quad({
                left: { field: "left" }, bottom: { field: "bottom" },
                right: { field: "right" }, top: { field: "top" },
                line_color: null, fill_color: palette[i % palette.length],
            });
            const r1 = new models_1.GlyphRenderer({ data_source: source, glyph: g1 });
            renderers.push(r1);
        }
    }
    if (orientation == "vertical") {
        [xdr, ydr] = [ydr, xdr];
        [xaxis, yaxis] = [yaxis, xaxis];
        [xscale, yscale] = [yscale, xscale];
        for (const r of renderers) {
            const data = r.data_source.data;
            [data.left, data.bottom] = [data.bottom, data.left];
            [data.right, data.top] = [data.top, data.right];
        }
    }
    const plot = new models_1.Plot({ x_range: xdr, y_range: ydr, x_scale: xscale, y_scale: yscale });
    if (opts.width != null)
        plot.plot_width = opts.width;
    if (opts.height != null)
        plot.plot_height = opts.height;
    plot.add_renderers(...renderers);
    plot.add_layout(yaxis, "left");
    plot.add_layout(xaxis, "below");
    const tooltip = "<div>@labels</div><div>@columns:&nbsp<b>@values</b></div>";
    let anchor;
    let attachment;
    if (orientation == "horizontal") {
        anchor = "center_right";
        attachment = "horizontal";
    }
    else {
        anchor = "top_center";
        attachment = "vertical";
    }
    const hover = new models_1.HoverTool({
        renderers,
        tooltips: tooltip,
        point_policy: "snap_to_data",
        anchor,
        attachment,
    });
    plot.add_tools(hover);
    return plot;
}
exports.bar = bar;
