"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const box_1 = require("./box");
const p = require("../../core/properties");
class HBarView extends box_1.BoxView {
    scenterx(i) {
        return (this.sleft[i] + this.sright[i]) / 2;
    }
    scentery(i) {
        return this.sy[i];
    }
    _index_data() {
        return this._index_box(this._y.length);
    }
    _lrtb(i) {
        const l = Math.min(this._left[i], this._right[i]);
        const r = Math.max(this._left[i], this._right[i]);
        const t = this._y[i] + 0.5 * this._height[i];
        const b = this._y[i] - 0.5 * this._height[i];
        return [l, r, t, b];
    }
    _map_data() {
        this.sy = this.renderer.yscale.v_compute(this._y);
        this.sh = this.sdist(this.renderer.yscale, this._y, this._height, "center");
        this.sleft = this.renderer.xscale.v_compute(this._left);
        this.sright = this.renderer.xscale.v_compute(this._right);
        const n = this.sy.length;
        this.stop = new Float64Array(n);
        this.sbottom = new Float64Array(n);
        for (let i = 0; i < n; i++) {
            this.stop[i] = this.sy[i] - this.sh[i] / 2;
            this.sbottom[i] = this.sy[i] + this.sh[i] / 2;
        }
        this._clamp_viewport();
    }
}
exports.HBarView = HBarView;
HBarView.__name__ = "HBarView";
class HBar extends box_1.Box {
    constructor(attrs) {
        super(attrs);
    }
    static init_HBar() {
        this.prototype.default_view = HBarView;
        this.coords([['left', 'y']]);
        this.define({
            height: [p.NumberSpec],
            right: [p.CoordinateSpec],
        });
        this.override({ left: 0 });
    }
}
exports.HBar = HBar;
HBar.__name__ = "HBar";
HBar.init_HBar();
