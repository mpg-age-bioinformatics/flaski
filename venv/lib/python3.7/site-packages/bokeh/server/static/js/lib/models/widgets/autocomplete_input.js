"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const text_input_1 = require("./text_input");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const math_1 = require("../../core/util/math");
const mixins_1 = require("../../styles/mixins");
const menus_1 = require("../../styles/menus");
class AutocompleteInputView extends text_input_1.TextInputView {
    constructor() {
        super(...arguments);
        this._open = false;
        this._last_value = "";
        this._hover_index = 0;
    }
    render() {
        super.render();
        this.input_el.addEventListener("keydown", (event) => this._keydown(event));
        this.input_el.addEventListener("keyup", (event) => this._keyup(event));
        this.menu = dom_1.div({ class: [menus_1.bk_menu, mixins_1.bk_below] });
        this.menu.addEventListener("click", (event) => this._menu_click(event));
        this.menu.addEventListener("mouseover", (event) => this._menu_hover(event));
        this.el.appendChild(this.menu);
        dom_1.undisplay(this.menu);
    }
    change_input() {
        if (this._open && this.menu.children.length > 0) {
            this.model.value = this.menu.children[this._hover_index].textContent;
            this.input_el.focus();
            this._hide_menu();
        }
    }
    _update_completions(completions) {
        dom_1.empty(this.menu);
        for (const text of completions) {
            const item = dom_1.div({}, text);
            this.menu.appendChild(item);
        }
        if (completions.length > 0)
            this.menu.children[0].classList.add(mixins_1.bk_active);
    }
    _show_menu() {
        if (!this._open) {
            this._open = true;
            this._hover_index = 0;
            this._last_value = this.model.value;
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
    _menu_click(event) {
        if (event.target != event.currentTarget && event.target instanceof Element) {
            this.model.value = event.target.textContent;
            this.input_el.focus();
            this._hide_menu();
        }
    }
    _menu_hover(event) {
        if (event.target != event.currentTarget && event.target instanceof Element) {
            let i = 0;
            for (i = 0; i < this.menu.children.length; i++) {
                if (this.menu.children[i].textContent == event.target.textContent)
                    break;
            }
            this._bump_hover(i);
        }
    }
    _bump_hover(new_index) {
        const n_children = this.menu.children.length;
        if (this._open && n_children > 0) {
            this.menu.children[this._hover_index].classList.remove(mixins_1.bk_active);
            this._hover_index = math_1.clamp(new_index, 0, n_children - 1);
            this.menu.children[this._hover_index].classList.add(mixins_1.bk_active);
        }
    }
    _keydown(_event) { }
    _keyup(event) {
        switch (event.keyCode) {
            case dom_1.Keys.Enter: {
                this.change_input();
                break;
            }
            case dom_1.Keys.Esc: {
                this._hide_menu();
                break;
            }
            case dom_1.Keys.Up: {
                this._bump_hover(this._hover_index - 1);
                break;
            }
            case dom_1.Keys.Down: {
                this._bump_hover(this._hover_index + 1);
                break;
            }
            default: {
                const value = this.input_el.value;
                if (value.length < this.model.min_characters) {
                    this._hide_menu();
                    return;
                }
                const completions = [];
                for (const text of this.model.completions) {
                    if (text.startsWith(value))
                        completions.push(text);
                }
                this._update_completions(completions);
                if (completions.length == 0)
                    this._hide_menu();
                else
                    this._show_menu();
            }
        }
    }
}
exports.AutocompleteInputView = AutocompleteInputView;
AutocompleteInputView.__name__ = "AutocompleteInputView";
class AutocompleteInput extends text_input_1.TextInput {
    constructor(attrs) {
        super(attrs);
    }
    static init_AutocompleteInput() {
        this.prototype.default_view = AutocompleteInputView;
        this.define({
            completions: [p.Array, []],
            min_characters: [p.Int, 2],
        });
    }
}
exports.AutocompleteInput = AutocompleteInput;
AutocompleteInput.__name__ = "AutocompleteInput";
AutocompleteInput.init_AutocompleteInput();
