"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const button_tool_1 = require("./button_tool");
const mixins_1 = require("../../styles/mixins");
class OnOffButtonView extends button_tool_1.ButtonToolButtonView {
    render() {
        super.render();
        if (this.model.active)
            this.el.classList.add(mixins_1.bk_active);
        else
            this.el.classList.remove(mixins_1.bk_active);
    }
    _clicked() {
        const active = this.model.active;
        this.model.active = !active;
    }
}
exports.OnOffButtonView = OnOffButtonView;
OnOffButtonView.__name__ = "OnOffButtonView";
