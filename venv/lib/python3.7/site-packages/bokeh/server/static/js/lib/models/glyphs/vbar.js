"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const box_1 = require("./box");
const p = require("../../core/properties");
class VBarView extends box_1.BoxView {
    scenterx(i) {
        return this.sx[i];
    }
    scentery(i) {
        return (this.stop[i] + this.sbottom[i]) / 2;
    }
    _index_data() {
        return this._index_box(this._x.length);
    }
    _lrtb(i) {
        const l = this._x[i] - (this._width[i] / 2);
        const r = this._x[i] + (this._width[i] / 2);
        const t = Math.max(this._top[i], this._bottom[i]);
        const b = Math.min(this._top[i], this._bottom[i]);
        return [l, r, t, b];
    }
    _map_data() {
        this.sx = this.renderer.xscale.v_compute(this._x);
        this.sw = this.sdist(this.renderer.xscale, this._x, this._width, "center");
        this.stop = this.renderer.yscale.v_compute(this._top);
        this.sbottom = this.renderer.yscale.v_compute(this._bottom);
        const n = this.sx.length;
        this.sleft = new Float64Array(n);
        this.sright = new Float64Array(n);
        for (let i = 0; i < n; i++) {
            this.sleft[i] = this.sx[i] - this.sw[i] / 2;
            this.sright[i] = this.sx[i] + this.sw[i] / 2;
        }
        this._clamp_viewport();
    }
}
exports.VBarView = VBarView;
VBarView.__name__ = "VBarView";
class VBar extends box_1.Box {
    constructor(attrs) {
        super(attrs);
    }
    static init_VBar() {
        this.prototype.default_view = VBarView;
        this.coords([['x', 'bottom']]);
        this.define({
            width: [p.NumberSpec],
            top: [p.CoordinateSpec],
        });
        this.override({
            bottom: 0,
        });
    }
}
exports.VBar = VBar;
VBar.__name__ = "VBar";
VBar.init_VBar();
