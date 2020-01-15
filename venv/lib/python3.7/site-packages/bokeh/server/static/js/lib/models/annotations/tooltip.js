"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const annotation_1 = require("./annotation");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const tooltips_1 = require("../../styles/tooltips");
const mixins_1 = require("../../styles/mixins");
function compute_side(attachment, sx, sy, hcenter, vcenter) {
    switch (attachment) {
        case "horizontal":
            return sx < hcenter ? "right" : "left";
        case "vertical":
            return sy < vcenter ? "below" : "above";
        default:
            return attachment;
    }
}
exports.compute_side = compute_side;
class TooltipView extends annotation_1.AnnotationView {
    initialize() {
        super.initialize();
        // TODO (bev) really probably need multiple divs
        this.plot_view.canvas_overlays.appendChild(this.el);
        dom_1.undisplay(this.el);
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.properties.data.change, () => this._draw_tips());
    }
    css_classes() {
        return super.css_classes().concat(tooltips_1.bk_tooltip);
    }
    render() {
        if (!this.model.visible)
            return;
        this._draw_tips();
    }
    _draw_tips() {
        const { data } = this.model;
        dom_1.empty(this.el);
        dom_1.undisplay(this.el);
        if (this.model.custom)
            this.el.classList.add(tooltips_1.bk_tooltip_custom);
        else
            this.el.classList.remove(tooltips_1.bk_tooltip_custom);
        if (data.length == 0)
            return;
        const { frame } = this.plot_view;
        for (const [sx, sy, content] of data) {
            if (this.model.inner_only && !frame.bbox.contains(sx, sy))
                continue;
            const tip = dom_1.div({}, content);
            this.el.appendChild(tip);
        }
        const [sx, sy] = data[data.length - 1]; // XXX: this previously depended on {sx, sy} leaking from the for-loop
        const side = compute_side(this.model.attachment, sx, sy, frame._hcenter.value, frame._vcenter.value);
        this.el.classList.remove(mixins_1.bk_right);
        this.el.classList.remove(mixins_1.bk_left);
        this.el.classList.remove(mixins_1.bk_above);
        this.el.classList.remove(mixins_1.bk_below);
        const arrow_size = 10; // XXX: keep in sync with less
        dom_1.display(this.el); // XXX: {offset,client}Width() gives 0 when display="none"
        // slightly confusing: side "left" (for example) is relative to point that
        // is being annotated but CS class ".bk-left" is relative to the tooltip itself
        let left, top;
        switch (side) {
            case "right":
                this.el.classList.add(mixins_1.bk_left);
                left = sx + (this.el.offsetWidth - this.el.clientWidth) + arrow_size;
                top = sy - this.el.offsetHeight / 2;
                break;
            case "left":
                this.el.classList.add(mixins_1.bk_right);
                left = sx - this.el.offsetWidth - arrow_size;
                top = sy - this.el.offsetHeight / 2;
                break;
            case "below":
                this.el.classList.add(mixins_1.bk_above);
                top = sy + (this.el.offsetHeight - this.el.clientHeight) + arrow_size;
                left = Math.round(sx - this.el.offsetWidth / 2);
                break;
            case "above":
                this.el.classList.add(mixins_1.bk_below);
                top = sy - this.el.offsetHeight - arrow_size;
                left = Math.round(sx - this.el.offsetWidth / 2);
                break;
            default:
                throw new Error("unreachable code");
        }
        if (this.model.show_arrow)
            this.el.classList.add(tooltips_1.bk_tooltip_arrow);
        // TODO (bev) this is not currently bulletproof. If there are
        // two hits, not colocated and one is off the screen, that can
        // be problematic
        if (this.el.childNodes.length > 0) {
            this.el.style.top = `${top}px`;
            this.el.style.left = `${left}px`;
        }
        else
            dom_1.undisplay(this.el);
    }
}
exports.TooltipView = TooltipView;
TooltipView.__name__ = "TooltipView";
class Tooltip extends annotation_1.Annotation {
    constructor(attrs) {
        super(attrs);
    }
    static init_Tooltip() {
        this.prototype.default_view = TooltipView;
        this.define({
            attachment: [p.TooltipAttachment, 'horizontal'],
            inner_only: [p.Boolean, true],
            show_arrow: [p.Boolean, true],
        });
        this.override({
            level: 'overlay',
        });
        this.internal({
            data: [p.Any, []],
            custom: [p.Any],
        });
    }
    clear() {
        this.data = [];
    }
    add(sx, sy, content) {
        this.data = this.data.concat([[sx, sy, content]]);
    }
}
exports.Tooltip = Tooltip;
Tooltip.__name__ = "Tooltip";
Tooltip.init_Tooltip();
