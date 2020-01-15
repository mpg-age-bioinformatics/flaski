"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const model_1 = require("../../model");
const p = require("../../core/properties");
class Texture extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_Texture() {
        this.define({
            repetition: [p.TextureRepetition, "repeat"],
        });
    }
    onload(defer_func) {
        defer_func();
    }
}
exports.Texture = Texture;
Texture.__name__ = "Texture";
Texture.init_Texture();
