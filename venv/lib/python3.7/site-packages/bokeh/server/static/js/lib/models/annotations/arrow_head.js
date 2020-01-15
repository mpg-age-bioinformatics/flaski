"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const annotation_1 = require("./annotation");
const visuals_1 = require("../../core/visuals");
const p = require("../../core/properties");
class ArrowHead extends annotation_1.Annotation {
    constructor(attrs) {
        super(attrs);
    }
    static init_ArrowHead() {
        this.define({
            size: [p.Number, 25],
        });
    }
    initialize() {
        super.initialize();
        this.visuals = new visuals_1.Visuals(this);
    }
}
exports.ArrowHead = ArrowHead;
ArrowHead.__name__ = "ArrowHead";
ArrowHead.init_ArrowHead();
class OpenHead extends ArrowHead {
    constructor(attrs) {
        super(attrs);
    }
    static init_OpenHead() {
        this.mixins(['line']);
    }
    clip(ctx, i) {
        // This method should not begin or close a path
        this.visuals.line.set_vectorize(ctx, i);
        ctx.moveTo(0.5 * this.size, this.size);
        ctx.lineTo(0.5 * this.size, -2);
        ctx.lineTo(-0.5 * this.size, -2);
        ctx.lineTo(-0.5 * this.size, this.size);
        ctx.lineTo(0, 0);
        ctx.lineTo(0.5 * this.size, this.size);
    }
    render(ctx, i) {
        if (this.visuals.line.doit) {
            this.visuals.line.set_vectorize(ctx, i);
            ctx.beginPath();
            ctx.moveTo(0.5 * this.size, this.size);
            ctx.lineTo(0, 0);
            ctx.lineTo(-0.5 * this.size, this.size);
            ctx.stroke();
        }
    }
}
exports.OpenHead = OpenHead;
OpenHead.__name__ = "OpenHead";
OpenHead.init_OpenHead();
class NormalHead extends ArrowHead {
    constructor(attrs) {
        super(attrs);
    }
    static init_NormalHead() {
        this.mixins(['line', 'fill']);
        this.override({
            fill_color: 'black',
        });
    }
    clip(ctx, i) {
        // This method should not begin or close a path
        this.visuals.line.set_vectorize(ctx, i);
        ctx.moveTo(0.5 * this.size, this.size);
        ctx.lineTo(0.5 * this.size, -2);
        ctx.lineTo(-0.5 * this.size, -2);
        ctx.lineTo(-0.5 * this.size, this.size);
        ctx.lineTo(0.5 * this.size, this.size);
    }
    render(ctx, i) {
        if (this.visuals.fill.doit) {
            this.visuals.fill.set_vectorize(ctx, i);
            this._normal(ctx, i);
            ctx.fill();
        }
        if (this.visuals.line.doit) {
            this.visuals.line.set_vectorize(ctx, i);
            this._normal(ctx, i);
            ctx.stroke();
        }
    }
    _normal(ctx, _i) {
        ctx.beginPath();
        ctx.moveTo(0.5 * this.size, this.size);
        ctx.lineTo(0, 0);
        ctx.lineTo(-0.5 * this.size, this.size);
        ctx.closePath();
    }
}
exports.NormalHead = NormalHead;
NormalHead.__name__ = "NormalHead";
NormalHead.init_NormalHead();
class VeeHead extends ArrowHead {
    constructor(attrs) {
        super(attrs);
    }
    static init_VeeHead() {
        this.mixins(['line', 'fill']);
        this.override({
            fill_color: 'black',
        });
    }
    clip(ctx, i) {
        // This method should not begin or close a path
        this.visuals.line.set_vectorize(ctx, i);
        ctx.moveTo(0.5 * this.size, this.size);
        ctx.lineTo(0.5 * this.size, -2);
        ctx.lineTo(-0.5 * this.size, -2);
        ctx.lineTo(-0.5 * this.size, this.size);
        ctx.lineTo(0, 0.5 * this.size);
        ctx.lineTo(0.5 * this.size, this.size);
    }
    render(ctx, i) {
        if (this.visuals.fill.doit) {
            this.visuals.fill.set_vectorize(ctx, i);
            this._vee(ctx, i);
            ctx.fill();
        }
        if (this.visuals.line.doit) {
            this.visuals.line.set_vectorize(ctx, i);
            this._vee(ctx, i);
            ctx.stroke();
        }
    }
    _vee(ctx, _i) {
        ctx.beginPath();
        ctx.moveTo(0.5 * this.size, this.size);
        ctx.lineTo(0, 0);
        ctx.lineTo(-0.5 * this.size, this.size);
        ctx.lineTo(0, 0.5 * this.size);
        ctx.closePath();
    }
}
exports.VeeHead = VeeHead;
VeeHead.__name__ = "VeeHead";
VeeHead.init_VeeHead();
class TeeHead extends ArrowHead {
    constructor(attrs) {
        super(attrs);
    }
    static init_TeeHead() {
        this.mixins(['line']);
    }
    render(ctx, i) {
        if (this.visuals.line.doit) {
            this.visuals.line.set_vectorize(ctx, i);
            ctx.beginPath();
            ctx.moveTo(0.5 * this.size, 0);
            ctx.lineTo(-0.5 * this.size, 0);
            ctx.stroke();
        }
    }
    clip(_ctx, _i) { }
}
exports.TeeHead = TeeHead;
TeeHead.__name__ = "TeeHead";
TeeHead.init_TeeHead();
