"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const layoutable_1 = require("./layoutable");
const types_1 = require("./types");
const dom_1 = require("../dom");
class ContentBox extends layoutable_1.ContentLayoutable {
    constructor(el) {
        super();
        this.content_size = dom_1.unsized(el, () => new types_1.Sizeable(dom_1.size(el)));
    }
    _content_size() {
        return this.content_size;
    }
}
exports.ContentBox = ContentBox;
ContentBox.__name__ = "ContentBox";
class VariadicBox extends layoutable_1.Layoutable {
    constructor(el) {
        super();
        this.el = el;
    }
    _measure(viewport) {
        const bounded = new types_1.Sizeable(viewport).bounded_to(this.sizing.size);
        return dom_1.sized(this.el, bounded, () => {
            const content = new types_1.Sizeable(dom_1.content_size(this.el));
            const { border, padding } = dom_1.extents(this.el);
            return content.grow_by(border).grow_by(padding).map(Math.ceil);
        });
    }
}
exports.VariadicBox = VariadicBox;
VariadicBox.__name__ = "VariadicBox";
