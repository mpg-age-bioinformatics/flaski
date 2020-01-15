"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const widget_1 = require("../widget");
const cds_view_1 = require("../../sources/cds_view");
const p = require("../../../core/properties");
class TableWidget extends widget_1.Widget {
    constructor(attrs) {
        super(attrs);
    }
    static init_TableWidget() {
        this.define({
            source: [p.Instance],
            view: [p.Instance, () => new cds_view_1.CDSView()],
        });
    }
    initialize() {
        super.initialize();
        if (this.view.source == null) {
            this.view.source = this.source;
            this.view.compute_indices();
        }
    }
}
exports.TableWidget = TableWidget;
TableWidget.__name__ = "TableWidget";
TableWidget.init_TableWidget();
