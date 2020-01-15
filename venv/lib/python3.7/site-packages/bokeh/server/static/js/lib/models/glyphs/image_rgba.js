"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const image_base_1 = require("./image_base");
const array_1 = require("../../core/util/array");
class ImageRGBAView extends image_base_1.ImageBaseView {
    initialize() {
        super.initialize();
        this.connect(this.model.properties.global_alpha.change, () => this.renderer.request_render());
    }
    _set_data(indices) {
        this._set_width_heigh_data();
        for (let i = 0, end = this._image.length; i < end; i++) {
            if (indices != null && indices.indexOf(i) < 0)
                continue;
            let buf;
            if (this._image_shape != null && this._image_shape[i].length > 0) {
                buf = this._image[i].buffer;
                const shape = this._image_shape[i];
                this._height[i] = shape[0];
                this._width[i] = shape[1];
            }
            else {
                const _image = this._image[i];
                const flat = array_1.concat(_image);
                buf = new ArrayBuffer(flat.length * 4);
                const color = new Uint32Array(buf);
                for (let j = 0, endj = flat.length; j < endj; j++) {
                    color[j] = flat[j];
                }
                this._height[i] = _image.length;
                this._width[i] = _image[0].length;
            }
            const buf8 = new Uint8Array(buf);
            this._set_image_data_from_buffer(i, buf8);
        }
    }
    _render(ctx, indices, { image_data, sx, sy, sw, sh }) {
        const old_smoothing = ctx.getImageSmoothingEnabled();
        ctx.setImageSmoothingEnabled(false);
        ctx.globalAlpha = this.model.global_alpha;
        for (const i of indices) {
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
exports.ImageRGBAView = ImageRGBAView;
ImageRGBAView.__name__ = "ImageRGBAView";
class ImageRGBA extends image_base_1.ImageBase {
    constructor(attrs) {
        super(attrs);
    }
    static init_ImageRGBA() {
        this.prototype.default_view = ImageRGBAView;
    }
}
exports.ImageRGBA = ImageRGBA;
ImageRGBA.__name__ = "ImageRGBA";
ImageRGBA.init_ImageRGBA();
