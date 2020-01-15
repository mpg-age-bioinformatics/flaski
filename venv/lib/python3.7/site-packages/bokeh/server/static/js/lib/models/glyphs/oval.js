"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const ellipse_oval_1 = require("./ellipse_oval");
class OvalView extends ellipse_oval_1.EllipseOvalView {
    _map_data() {
        let sw;
        const n = this._x.length;
        this.sw = new Float64Array(n);
        if (this.model.properties.width.units == "data")
            sw = this.sdist(this.renderer.xscale, this._x, this._width, 'center');
        else
            sw = this._width;
        // oval drawn from bezier curves = ellipse with width reduced by 3/4
        for (let i = 0; i < n; i++)
            this.sw[i] = sw[i] * 0.75;
        if (this.model.properties.height.units == "data")
            this.sh = this.sdist(this.renderer.yscale, this._y, this._height, 'center');
        else
            this.sh = this._height;
    }
}
exports.OvalView = OvalView;
OvalView.__name__ = "OvalView";
class Oval extends ellipse_oval_1.EllipseOval {
    constructor(attrs) {
        super(attrs);
    }
    static init_Oval() {
        this.prototype.default_view = OvalView;
    }
}
exports.Oval = Oval;
Oval.__name__ = "Oval";
Oval.init_Oval();
