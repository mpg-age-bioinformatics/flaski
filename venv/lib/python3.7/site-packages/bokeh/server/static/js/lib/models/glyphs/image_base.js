"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const xy_glyph_1 = require("./xy_glyph");
const p = require("../../core/properties");
const hittest = require("../../core/hittest");
const spatial_1 = require("../../core/util/spatial");
class ImageBaseView extends xy_glyph_1.XYGlyphView {
    _render(_ctx, _indices, _data) { }
    _index_data() {
        const points = [];
        for (let i = 0, end = this._x.length; i < end; i++) {
            const [l, r, t, b] = this._lrtb(i);
            if (isNaN(l + r + t + b) || !isFinite(l + r + t + b)) {
                continue;
            }
            points.push({ x0: l, y0: b, x1: r, y1: t, i });
        }
        return new spatial_1.SpatialIndex(points);
    }
    _lrtb(i) {
        const xr = this.renderer.xscale.source_range;
        const x1 = this._x[i];
        const x2 = xr.is_reversed ? x1 - this._dw[i] : x1 + this._dw[i];
        const yr = this.renderer.yscale.source_range;
        const y1 = this._y[i];
        const y2 = yr.is_reversed ? y1 - this._dh[i] : y1 + this._dh[i];
        const [l, r] = x1 < x2 ? [x1, x2] : [x2, x1];
        const [b, t] = y1 < y2 ? [y1, y2] : [y2, y1];
        return [l, r, t, b];
    }
    _set_width_heigh_data() {
        if (this.image_data == null || this.image_data.length != this._image.length)
            this.image_data = new Array(this._image.length);
        if (this._width == null || this._width.length != this._image.length)
            this._width = new Array(this._image.length);
        if (this._height == null || this._height.length != this._image.length)
            this._height = new Array(this._image.length);
    }
    _get_or_create_canvas(i) {
        const _image_data = this.image_data[i];
        if (_image_data != null && _image_data.width == this._width[i] &&
            _image_data.height == this._height[i])
            return _image_data;
        else {
            const canvas = document.createElement('canvas');
            canvas.width = this._width[i];
            canvas.height = this._height[i];
            return canvas;
        }
    }
    _set_image_data_from_buffer(i, buf8) {
        const canvas = this._get_or_create_canvas(i);
        const ctx = canvas.getContext('2d');
        const image_data = ctx.getImageData(0, 0, this._width[i], this._height[i]);
        image_data.data.set(buf8);
        ctx.putImageData(image_data, 0, 0);
        this.image_data[i] = canvas;
    }
    _map_data() {
        switch (this.model.properties.dw.units) {
            case "data": {
                this.sw = this.sdist(this.renderer.xscale, this._x, this._dw, 'edge', this.model.dilate);
                break;
            }
            case "screen": {
                this.sw = this._dw;
                break;
            }
        }
        switch (this.model.properties.dh.units) {
            case "data": {
                this.sh = this.sdist(this.renderer.yscale, this._y, this._dh, 'edge', this.model.dilate);
                break;
            }
            case "screen": {
                this.sh = this._dh;
                break;
            }
        }
    }
    _image_index(index, x, y) {
        const [l, r, t, b] = this._lrtb(index);
        const width = this._width[index];
        const height = this._height[index];
        const dx = (r - l) / width;
        const dy = (t - b) / height;
        let dim1 = Math.floor((x - l) / dx);
        let dim2 = Math.floor((y - b) / dy);
        if (this.renderer.xscale.source_range.is_reversed)
            dim1 = width - dim1 - 1;
        if (this.renderer.yscale.source_range.is_reversed)
            dim2 = height - dim2 - 1;
        return { index, dim1, dim2, flat_index: dim2 * width + dim1 };
    }
    _hit_point(geometry) {
        const { sx, sy } = geometry;
        const x = this.renderer.xscale.invert(sx);
        const y = this.renderer.yscale.invert(sy);
        const candidates = this.index.indices({ x0: x, x1: x, y0: y, y1: y });
        const result = hittest.create_empty_hit_test_result();
        result.image_indices = [];
        for (const index of candidates) {
            if ((sx != Infinity) && (sy != Infinity)) {
                result.image_indices.push(this._image_index(index, x, y));
            }
        }
        return result;
    }
}
exports.ImageBaseView = ImageBaseView;
ImageBaseView.__name__ = "ImageBaseView";
class ImageBase extends xy_glyph_1.XYGlyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_ImageBase() {
        this.prototype.default_view = ImageBaseView;
        this.define({
            image: [p.NumberSpec],
            dw: [p.DistanceSpec],
            dh: [p.DistanceSpec],
            dilate: [p.Boolean, false],
            global_alpha: [p.Number, 1.0],
        });
    }
}
exports.ImageBase = ImageBase;
ImageBase.__name__ = "ImageBase";
ImageBase.init_ImageBase();
