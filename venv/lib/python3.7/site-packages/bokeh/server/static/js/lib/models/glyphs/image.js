"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const image_base_1 = require("./image_base");
const linear_color_mapper_1 = require("../mappers/linear_color_mapper");
const p = require("../../core/properties");
const array_1 = require("../../core/util/array");
class ImageView extends image_base_1.ImageBaseView {
    initialize() {
        super.initialize();
        this.connect(this.model.color_mapper.change, () => this._update_image());
        this.connect(this.model.properties.global_alpha.change, () => this.renderer.request_render());
    }
    _update_image() {
        // Only reset image_data if already initialized
        if (this.image_data != null) {
            this._set_data();
            this.renderer.plot_view.request_render();
        }
    }
    _set_data() {
        this._set_width_heigh_data();
        const cmap = this.model.color_mapper.rgba_mapper;
        for (let i = 0, end = this._image.length; i < end; i++) {
            let img;
            if (this._image_shape != null && this._image_shape[i].length > 0) {
                img = this._image[i];
                const shape = this._image_shape[i];
                this._height[i] = shape[0];
                this._width[i] = shape[1];
            }
            else {
                const _image = this._image[i];
                img = array_1.concat(_image);
                this._height[i] = _image.length;
                this._width[i] = _image[0].length;
            }
            const buf8 = cmap.v_compute(img);
            this._set_image_data_from_buffer(i, buf8);
        }
    }
    _render(ctx, indices, { image_data, sx, sy, sw, sh }) {
        const old_smoothing = ctx.getImageSmoothingEnabled();
        ctx.setImageSmoothingEnabled(false);
        ctx.globalAlpha = this.model.global_alpha;
        for (const i of indices) {
            if (image_data[i] == null)
                continue;
            if (isNaN(sx[i] + sy[i] + sw[i] + sh[i]))
                continue;
            const y_offset = sy[i];
            ctx.translate(0, y_offset);
            ctx.scale(1, -1);
            ctx.translate(0, -y_offset);
            ctx.drawImage(image_data[i], sx[i] | 0, sy[i] | 0, sw[i], sh[i]);
            ctx.translate(0, y_offset);
            ctx.scale(1, -1);
            ctx.translate(0, -y_offset);
        }
        ctx.setImageSmoothingEnabled(old_smoothing);
    }
}
exports.ImageView = ImageView;
ImageView.__name__ = "ImageView";
// NOTE: this needs to be redefined here, because palettes are located in bokeh-api.js bundle
const Greys9 = () => ["#000000", "#252525", "#525252", "#737373", "#969696", "#bdbdbd", "#d9d9d9", "#f0f0f0", "#ffffff"];
class Image extends image_base_1.ImageBase {
    constructor(attrs) {
        super(attrs);
    }
    static init_Image() {
        this.prototype.default_view = ImageView;
        this.define({
            color_mapper: [p.Instance, () => new linear_color_mapper_1.LinearColorMapper({ palette: Greys9() })],
        });
    }
}
exports.Image = Image;
Image.__name__ = "Image";
Image.init_Image();
