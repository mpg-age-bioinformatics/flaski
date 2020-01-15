"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const has_props_1 = require("../../core/has_props");
const dom_view_1 = require("../../core/dom_view");
const logging_1 = require("../../core/logging");
const p = require("../../core/properties");
const dom_1 = require("../../core/dom");
const bbox_1 = require("../../core/util/bbox");
const compat_1 = require("../../core/util/compat");
const canvas_1 = require("../../core/util/canvas");
const canvas_2 = require("../../styles/canvas");
// fixes up a problem with some versions of IE11
// ref: http://stackoverflow.com/questions/22062313/imagedata-set-in-internetexplorer
if (compat_1.is_ie && typeof CanvasPixelArray !== "undefined") {
    CanvasPixelArray.prototype.set = function (arr) {
        for (let i = 0; i < this.length; i++) {
            this[i] = arr[i];
        }
    };
}
const canvas2svg = require("canvas2svg");
class CanvasView extends dom_view_1.DOMView {
    get ctx() {
        return this._ctx;
    }
    initialize() {
        super.initialize();
        this.map_el = this.model.map ? this.el.appendChild(dom_1.div({ class: canvas_2.bk_canvas_map })) : null;
        const style = {
            position: "absolute",
            top: "0",
            left: "0",
            width: "100%",
            height: "100%",
        };
        switch (this.model.output_backend) {
            case "canvas":
            case "webgl": {
                this.canvas_el = this.el.appendChild(dom_1.canvas({ class: canvas_2.bk_canvas, style }));
                const ctx = this.canvas_el.getContext('2d');
                if (ctx == null)
                    throw new Error("unable to obtain 2D rendering context");
                this._ctx = ctx;
                break;
            }
            case "svg": {
                const ctx = new canvas2svg();
                this._ctx = ctx;
                this.canvas_el = this.el.appendChild(ctx.getSvg());
                break;
            }
        }
        this.overlays_el = this.el.appendChild(dom_1.div({ class: canvas_2.bk_canvas_overlays, style }));
        this.events_el = this.el.appendChild(dom_1.div({ class: canvas_2.bk_canvas_events, style }));
        canvas_1.fixup_ctx(this._ctx);
        logging_1.logger.debug("CanvasView initialized");
    }
    get_canvas_element() {
        return this.canvas_el;
    }
    prepare_canvas(width, height) {
        // Ensure canvas has the correct size, taking HIDPI into account
        this.bbox = new bbox_1.BBox({ left: 0, top: 0, width, height });
        this.el.style.width = `${width}px`;
        this.el.style.height = `${height}px`;
        const pixel_ratio = canvas_1.get_scale_ratio(this.ctx, this.model.use_hidpi, this.model.output_backend);
        this.model.pixel_ratio = pixel_ratio;
        this.canvas_el.style.width = `${width}px`;
        this.canvas_el.style.height = `${height}px`;
        // XXX: io.export and canvas2svg don't like this
        // this.canvas_el.width = width*pixel_ratio
        // this.canvas_el.height = height*pixel_ratio
        this.canvas_el.setAttribute("width", `${width * pixel_ratio}`);
        this.canvas_el.setAttribute("height", `${height * pixel_ratio}`);
        logging_1.logger.debug(`Rendering CanvasView with width: ${width}, height: ${height}, pixel ratio: ${pixel_ratio}`);
    }
}
exports.CanvasView = CanvasView;
CanvasView.__name__ = "CanvasView";
class Canvas extends has_props_1.HasProps {
    constructor(attrs) {
        super(attrs);
    }
    static init_Canvas() {
        this.prototype.default_view = CanvasView;
        this.internal({
            map: [p.Boolean, false],
            use_hidpi: [p.Boolean, true],
            pixel_ratio: [p.Number, 1],
            output_backend: [p.OutputBackend, "canvas"],
        });
    }
}
exports.Canvas = Canvas;
Canvas.__name__ = "Canvas";
Canvas.init_Canvas();
