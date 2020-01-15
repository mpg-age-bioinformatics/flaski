"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const renderer_1 = require("./renderer");
class GuideRendererView extends renderer_1.RendererView {
}
exports.GuideRendererView = GuideRendererView;
GuideRendererView.__name__ = "GuideRendererView";
class GuideRenderer extends renderer_1.Renderer {
    constructor(attrs) {
        super(attrs);
    }
    static init_GuideRenderer() {
        this.override({
            level: "overlay",
        });
    }
}
exports.GuideRenderer = GuideRenderer;
GuideRenderer.__name__ = "GuideRenderer";
GuideRenderer.init_GuideRenderer();
