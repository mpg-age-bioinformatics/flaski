"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const abstract_button_1 = require("./abstract_button");
const bokeh_events_1 = require("../../core/bokeh_events");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const types_1 = require("../../core/util/types");
const mixins_1 = require("../../styles/mixins");
const buttons_1 = require("../../styles/buttons");
const menus_1 = require("../../styles/menus");
class DropdownView extends abstract_button_1.AbstractButtonView {
    constructor() {
        super(...arguments);
        this._open = false;
    }
    render() {
        super.render();
        const caret = dom_1.div({ class: [menus_1.bk_caret, mixins_1.bk_down] });
        if (!this.model.is_split)
            this.button_el.appendChild(caret);
        else {
            const toggle = this._render_button(caret);
            toggle.classList.add(buttons_1.bk_dropdown_toggle);
            toggle.addEventListener("click", () => this._toggle_menu());
            this.group_el.appendChild(toggle);
        }
        const items = this.model.menu.map((item, i) => {
            if (item == null)
                return dom_1.div({ class: menus_1.bk_divider });
            else {
                const label = types_1.isString(item) ? item : item[0];
                const el = dom_1.div({}, label);
                el.addEventListener("click", () => this._item_click(i));
                return el;
            }
        });
        this.menu = dom_1.div({ class: [menus_1.bk_menu, mixins_1.bk_below] }, items);
        this.el.appendChild(this.menu);
        dom_1.undisplay(this.menu);
    }
    _show_menu() {
        if (!this._open) {
            this._open = true;
            dom_1.display(this.menu);
            const listener = (event) => {
                const { target } = event;
                if (target instanceof HTMLElement && !this.el.contains(target)) {
                    document.removeEventListener("click", listener);
                    this._hide_menu();
                }
            };
            document.addEventListener("click", listener);
        }
    }
    _hide_menu() {
        if (this._open) {
            this._open = false;
            dom_1.undisplay(this.menu);
        }
    }
    _toggle_menu() {
        if (this._open)
            this._hide_menu();
        else
            this._show_menu();
    }
    click() {
        if (!this.model.is_split)
            this._toggle_menu();
        else {
            this._hide_menu();
            this.model.trigger_event(new bokeh_events_1.ButtonClick());
            this.model.value = this.model.default_value;
            if (this.model.callback != null)
                this.model.callback.execute(this.model);
            super.click();
        }
    }
    _item_click(i) {
        this._hide_menu();
        const item = this.model.menu[i];
        if (item != null) {
            const value_or_callback = types_1.isString(item) ? item : item[1];
            if (types_1.isString(value_or_callback)) {
                this.model.trigger_event(new bokeh_events_1.MenuItemClick(value_or_callback));
                this.model.value = value_or_callback;
                if (this.model.callback != null)
                    this.model.callback.execute(this.model); // XXX: {index: i, item: value_or_callback})
            }
            else {
                value_or_callback.execute(this.model, { index: i }); // TODO
                if (this.model.callback != null)
                    this.model.callback.execute(this.model); // XXX: {index: i})
            }
        }
    }
}
exports.DropdownView = DropdownView;
DropdownView.__name__ = "DropdownView";
class Dropdown extends abstract_button_1.AbstractButton {
    constructor(attrs) {
        super(attrs);
    }
    static init_Dropdown() {
        this.prototype.default_view = DropdownView;
        this.define({
            split: [p.Boolean, false],
            menu: [p.Array, []],
            value: [p.String],
            default_value: [p.String],
        });
        this.override({
            label: "Dropdown",
        });
    }
    get is_split() {
        return this.split || this.default_value != null;
    }
}
exports.Dropdown = Dropdown;
Dropdown.__name__ = "Dropdown";
Dropdown.init_Dropdown();
