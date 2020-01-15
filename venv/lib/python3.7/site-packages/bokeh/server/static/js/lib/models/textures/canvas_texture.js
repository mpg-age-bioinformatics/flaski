"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const texture_1 = require("./texture");
const p = require("../../core/properties");
const string_1 = require("../../core/util/string");
class CanvasTexture extends texture_1.Texture {
    constructor(attrs) {
        super(attrs);
    }
    static init_CanvasTexture() {
        this.define({
            code: [p.String],
        });
    }
    get func() {
        const code = string_1.use_strict(this.code);
        return new Function("ctx", "color", "scale", "weight", "require", "exports", code);
    }
    get_pattern(color, scale, weight) {
        return (ctx) => {
            const canvas = document.createElement('canvas');
            canvas.width = scale;
            canvas.height = scale;
            const pattern_ctx = canvas.getContext('2d');
            this.func.call(this, pattern_ctx, color, scale, weight, require, {});
            return ctx.createPattern(canvas, this.repetition);
        };
    }
}
exports.CanvasTexture = CanvasTexture;
CanvasTexture.__name__ = "CanvasTexture";
CanvasTexture.init_CanvasTexture();
