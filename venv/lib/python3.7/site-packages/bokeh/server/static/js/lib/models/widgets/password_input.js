"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const text_input_1 = require("./text_input");
class PasswordInputView extends text_input_1.TextInputView {
    render() {
        super.render();
        this.input_el.type = "password";
    }
}
exports.PasswordInputView = PasswordInputView;
PasswordInputView.__name__ = "PasswordInputView";
class PasswordInput extends text_input_1.TextInput {
    constructor(attrs) {
        super(attrs);
    }
    static init_PasswordInput() {
        this.prototype.default_view = PasswordInputView;
    }
}
exports.PasswordInput = PasswordInput;
PasswordInput.__name__ = "PasswordInput";
PasswordInput.init_PasswordInput();
