"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const control_1 = require("./control");
class InputGroupView extends control_1.ControlView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.change, () => this.render());
    }
}
exports.InputGroupView = InputGroupView;
InputGroupView.__name__ = "InputGroupView";
class InputGroup extends control_1.Control {
    constructor(attrs) {
        super(attrs);
    }
}
exports.InputGroup = InputGroup;
InputGroup.__name__ = "InputGroup";
