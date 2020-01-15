"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const ellipse_oval_1 = require("./ellipse_oval");
class EllipseView extends ellipse_oval_1.EllipseOvalView {
}
exports.EllipseView = EllipseView;
EllipseView.__name__ = "EllipseView";
class Ellipse extends ellipse_oval_1.EllipseOval {
    constructor(attrs) {
        super(attrs);
    }
    static init_Ellipse() {
        this.prototype.default_view = EllipseView;
    }
}
exports.Ellipse = Ellipse;
Ellipse.__name__ = "Ellipse";
Ellipse.init_Ellipse();
