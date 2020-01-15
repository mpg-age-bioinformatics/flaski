"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const renderer_1 = require("./renderer");
const p = require("../../core/properties");
class DataRendererView extends renderer_1.RendererView {
}
exports.DataRendererView = DataRendererView;
DataRendererView.__name__ = "DataRendererView";
class DataRenderer extends renderer_1.Renderer {
    constructor(attrs) {
        super(attrs);
    }
    static init_DataRenderer() {
        this.define({
            x_range_name: [p.String, 'default'],
            y_range_name: [p.String, 'default'],
        });
        this.override({
            level: 'glyph',
        });
    }
}
exports.DataRenderer = DataRenderer;
DataRenderer.__name__ = "DataRenderer";
DataRenderer.init_DataRenderer();
