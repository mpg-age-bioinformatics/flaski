"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const xy_glyph_1 = require("./xy_glyph");
const utils_1 = require("./utils");
const p = require("../../core/properties");
class StepView extends xy_glyph_1.XYGlyphView {
    _render(ctx, indices, { sx, sy }) {
        let drawing = false;
        let last_index = null;
        this.visuals.line.set_value(ctx);
        const L = indices.length;
        if (L < 2)
            return;
        ctx.beginPath();
        ctx.moveTo(sx[0], sy[0]);
        for (const i of indices) {
            let x1, x2;
            let y1, y2;
            switch (this.model.mode) {
                case "before": {
                    [x1, y1] = [sx[i - 1], sy[i]];
                    [x2, y2] = [sx[i], sy[i]];
                    break;
                }
                case "after": {
                    [x1, y1] = [sx[i], sy[i - 1]];
                    [x2, y2] = [sx[i], sy[i]];
                    break;
                }
                case "center": {
                    const xm = (sx[i - 1] + sx[i]) / 2;
                    [x1, y1] = [xm, sy[i - 1]];
                    [x2, y2] = [xm, sy[i]];
                    break;
                }
                default:
                    throw new Error("unexpected");
            }
            if (drawing) {
                if (!isFinite(sx[i] + sy[i])) {
                    ctx.stroke();
                    ctx.beginPath();
                    drawing = false;
                    last_index = i;
                    continue;
                }
                if (last_index != null && i - last_index > 1) {
                    ctx.stroke();
                    drawing = false;
                }
            }
            if (drawing) {
                ctx.lineTo(x1, y1);
                ctx.lineTo(x2, y2);
            }
            else {
                ctx.beginPath();
                ctx.moveTo(sx[i], sy[i]);
                drawing = true;
            }
            last_index = i;
        }
        ctx.lineTo(sx[L - 1], sy[L - 1]);
        ctx.stroke();
    }
    draw_legend_for_index(ctx, bbox, index) {
        utils_1.generic_line_legend(this.visuals, ctx, bbox, index);
    }
}
exports.StepView = StepView;
StepView.__name__ = "StepView";
class Step extends xy_glyph_1.XYGlyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_Step() {
        this.prototype.default_view = StepView;
        this.mixins(['line']);
        this.define({
            mode: [p.StepMode, "before"],
        });
    }
}
exports.Step = Step;
Step.__name__ = "Step";
Step.init_Step();
