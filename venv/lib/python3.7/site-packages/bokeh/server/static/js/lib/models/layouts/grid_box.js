"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const layout_dom_1 = require("./layout_dom");
const grid_1 = require("../../core/layout/grid");
const p = require("../../core/properties");
class GridBoxView extends layout_dom_1.LayoutDOMView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.properties.children.change, () => this.rebuild());
    }
    get child_models() {
        return this.model.children.map(([child]) => child);
    }
    _update_layout() {
        this.layout = new grid_1.Grid();
        this.layout.rows = this.model.rows;
        this.layout.cols = this.model.cols;
        this.layout.spacing = this.model.spacing;
        for (const [child, row, col, row_span, col_span] of this.model.children) {
            const child_view = this._child_views[child.id];
            this.layout.items.push({ layout: child_view.layout, row, col, row_span, col_span });
        }
        this.layout.set_sizing(this.box_sizing());
    }
}
exports.GridBoxView = GridBoxView;
GridBoxView.__name__ = "GridBoxView";
class GridBox extends layout_dom_1.LayoutDOM {
    constructor(attrs) {
        super(attrs);
    }
    static init_GridBox() {
        this.prototype.default_view = GridBoxView;
        this.define({
            children: [p.Array, []],
            rows: [p.Any, "auto"],
            cols: [p.Any, "auto"],
            spacing: [p.Any, 0],
        });
    }
}
exports.GridBox = GridBox;
GridBox.__name__ = "GridBox";
GridBox.init_GridBox();
