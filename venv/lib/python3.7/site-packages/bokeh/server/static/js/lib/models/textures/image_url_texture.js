"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const texture_1 = require("./texture");
const p = require("../../core/properties");
const image_1 = require("../../core/util/image");
class ImageURLTexture extends texture_1.Texture {
    constructor(attrs) {
        super(attrs);
    }
    static init_ImageURLTexture() {
        this.define({
            url: [p.String],
        });
    }
    initialize() {
        super.initialize();
        this._loader = new image_1.ImageLoader(this.url);
    }
    get_pattern(_color, _scale, _weight) {
        return (ctx) => {
            if (!this._loader.finished) {
                return null;
            }
            return ctx.createPattern(this._loader.image, this.repetition);
        };
    }
    onload(defer_func) {
        this._loader.promise.then(() => defer_func());
    }
}
exports.ImageURLTexture = ImageURLTexture;
ImageURLTexture.__name__ = "ImageURLTexture";
ImageURLTexture.init_ImageURLTexture();
